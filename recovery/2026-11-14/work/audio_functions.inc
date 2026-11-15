static int sco_write(int s, char *buf, int len)
{

	int r;

	if (s == -1) {
		ast_debug(3, "sco_write() not ready\n");
		return 0;
	}

	ast_debug(3, "sco_write()\n");

	r = send(s, buf, len, MSG_DONTWAIT | MSG_NOSIGNAL);
	if (r == -1) {
		ast_debug(3, "sco write error %d\n", errno);
		return 0;
	}

	return 1;

}

static struct ast_frame *mbl_read(struct ast_channel *ast)
{

	struct mbl_pvt *pvt = ast_channel_tech_pvt(ast);
	struct ast_frame *fr = &ast_null_frame;
	int r;

	ast_debug(3, "*** mbl_read()\n");

	while (ast_mutex_trylock(&pvt->lock)) {
		CHANNEL_DEADLOCK_AVOIDANCE(ast);
	}

	if (!pvt->owner || pvt->sco_socket == -1) {
		goto e_return;
	}

	memset(&pvt->fr, 0x00, sizeof(struct ast_frame));
	pvt->fr.frametype = AST_FRAME_VOICE;
	pvt->fr.subclass.format = DEVICE_FRAME_FORMAT;
	pvt->fr.src = "Mobile";
	pvt->fr.offset = AST_FRIENDLY_OFFSET;
	pvt->fr.mallocd = 0;
	pvt->fr.delivery.tv_sec = 0;
	pvt->fr.delivery.tv_usec = 0;
	pvt->fr.data.ptr = pvt->io_buf + AST_FRIENDLY_OFFSET;

	do {
		r = recv(pvt->sco_socket, pvt->fr.data.ptr, CHANNEL_FRAME_SIZE, MSG_DONTWAIT);
		if (r <= 0) {
			if (r == 0 || (errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR)) {
				ast_debug(1, "[%s] SCO audio closed (%d), waiting for a new connection\n",
					pvt->id, r == 0 ? 0 : errno);
				ast_channel_set_fd(ast, 0, -1);
				close(pvt->sco_socket);
				pvt->sco_socket = -1;
				pvt->sco_tx_size = 0;
				ast_smoother_reset(pvt->bt_in_smoother, CHANNEL_FRAME_SIZE);
			}

			/* A missing voice frame must not end the RFCOMM call. */
			fr = &ast_null_frame;
			goto e_return;
		}

		/* The socket carries signed 16-bit PCM, not on-air CVSD bytes. */
		if (r % 2) {
			fr = &ast_null_frame;
			goto e_return;
		}
		sco_observe_packet(pvt, r);
		pvt->fr.datalen = r;
		pvt->fr.samples = r / 2;

		if (pvt->do_alignment_detection)
			do_alignment_detection(pvt, pvt->fr.data.ptr, r);

		ast_smoother_feed(pvt->bt_in_smoother, &pvt->fr);
		fr = ast_smoother_read(pvt->bt_in_smoother);
	} while (fr == NULL);
	fr = ast_dsp_process(ast, pvt->dsp, fr);

	ast_mutex_unlock(&pvt->lock);

	return fr;

e_return:
	ast_mutex_unlock(&pvt->lock);
	return fr;
}

static int mbl_write(struct ast_channel *ast, struct ast_frame *frame)
{

	struct mbl_pvt *pvt = ast_channel_tech_pvt(ast);
	struct ast_frame *f;

	ast_debug(3, "*** mbl_write\n");

	if (frame->frametype != AST_FRAME_VOICE) {
		return 0;
	}

	while (ast_mutex_trylock(&pvt->lock)) {
		CHANNEL_DEADLOCK_AVOIDANCE(ast);
	}

	/* In particular for USB, wait for a received host packet. SCO_OPTIONS
	 * is a maximum, and the eSCO event describes the radio payload.
	 */
	if (pvt->sco_socket != -1 && pvt->sco_tx_size) {
		ast_smoother_feed(pvt->bt_out_smoother, frame);
		while ((f = ast_smoother_read(pvt->bt_out_smoother))) {
			sco_write(pvt->sco_socket, f->data.ptr, f->datalen);
		}
	}

	ast_mutex_unlock(&pvt->lock);

	return 0;

}

