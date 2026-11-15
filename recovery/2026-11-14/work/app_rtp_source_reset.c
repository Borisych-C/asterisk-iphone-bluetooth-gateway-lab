/*
 * Work around Debian/Ubuntu Asterisk's 2016_opus_plc.patch retaining a
 * translator's RTP sequence number across a signalled RTP source change.
 * Opt in per PJSIP channel with RtpSourceReset() before media starts.
 * Copyright (C) 2026. GPL-2.0-or-later, like the Asterisk module interface.
 */
#include "asterisk.h"
#include "asterisk/channel.h"
#include "asterisk/framehook.h"
#include "asterisk/module.h"
#include "asterisk/pbx.h"
#include "asterisk/translate.h"

static const char application[] = "RtpSourceReset";

/* Called with the channel locked, as guaranteed by the framehook API. */
static void reset_read_sequence(struct ast_channel *chan)
{
	struct ast_trans_pvt *path;

	for (path = ast_channel_readtrans(chan); path; path = path->next) {
		/* The distribution patch uses this out-of-range value for an
		 * uninitialised sequence history. Preserve actual RTP frame metadata.
		 */
		path->f.seqno = 0x10000;
	}
}

static struct ast_frame *source_event(struct ast_channel *chan,
	struct ast_frame *frame, enum ast_framehook_event event, void *data)
{
	struct ast_frame *current;

	(void) data;
	if (event != AST_FRAMEHOOK_EVENT_READ) {
		return frame;
	}
	for (current = frame; current; current = AST_LIST_NEXT(current, frame_list)) {
		if (current->frametype == AST_FRAME_CONTROL
			&& current->subclass.integer == AST_CONTROL_SRCCHANGE) {
			reset_read_sequence(chan);
		}
	}
	return frame;
}

static int source_consumes(void *data, enum ast_frame_type type)
{
	(void) data;
	return type == AST_FRAME_CONTROL;
}

static void source_destroy(void *data)
{
	ast_module_unref(data);
}

static int source_exec(struct ast_channel *chan, const char *data)
{
	int id;
	struct ast_framehook_interface hook = {
		.version = AST_FRAMEHOOK_INTERFACE_VERSION,
		.event_cb = source_event,
		.consume_cb = source_consumes,
		.destroy_cb = source_destroy,
		.data = AST_MODULE_SELF,
	};

	if (!ast_strlen_zero(data) || strcmp(ast_channel_tech(chan)->type, "PJSIP")) {
		ast_log(LOG_WARNING, "RtpSourceReset requires a PJSIP channel and no arguments\n");
		return -1;
	}
	ast_module_ref(AST_MODULE_SELF);
	ast_channel_lock(chan);
	id = ast_framehook_attach(chan, &hook);
	if (id >= 0) {
		reset_read_sequence(chan);
	}
	ast_channel_unlock(chan);
	if (id < 0) {
		ast_module_unref(AST_MODULE_SELF);
		return -1;
	}
	return 0;
}

static int unload_module(void)
{
	return ast_unregister_application(application);
}

static int load_module(void)
{
	return ast_register_application(application, source_exec,
		"Reset translator sequence history on an RTP source change",
		"RtpSourceReset(): Attach to a PJSIP channel before media starts.\n"
		"Workaround for Debian bug 1150408, without changing audio or SIP signalling.\n");
}

AST_MODULE_INFO_STANDARD(ASTERISK_GPL_KEY, "RTP source change translation reset");
