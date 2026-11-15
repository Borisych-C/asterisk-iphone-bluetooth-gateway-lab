from pathlib import Path
import difflib

root = Path(__file__).parent
s = (root / 'recovery.c').read_text()

def edit(old, new, count=1):
    global s
    assert s.count(old) == count, (old, s.count(old))
    s = s.replace(old, new)

edit('#define DEVICE_FRAME_SIZE 48\n', '')
edit('/* our bt_out_smoother, for making 48 byte frames */',
     '/* Packetizes outgoing PCM for the current host transport. */')
edit('int sco_socket;\t\t\t\t\t/* sco socket descriptor */',
     'int sco_socket;\t\t\t\t\t/* sco socket descriptor */\n\tuint16_t sco_mtu;\n\tuint16_t sco_tx_size;')
edit('static int sco_bind(struct adapter_pvt *adapter);',
     'static int sco_bind(struct adapter_pvt *adapter);\nstatic void sco_configure_socket(struct mbl_pvt *pvt);\nstatic void sco_observe_packet(struct mbl_pvt *pvt, unsigned int size);')
edit('ast_smoother_reset(pvt->bt_out_smoother, DEVICE_FRAME_SIZE);',
     'ast_smoother_reset(pvt->bt_out_smoother, pvt->sco_tx_size ? pvt->sco_tx_size : CHANNEL_FRAME_SIZE);')
edit('ast_smoother_new(DEVICE_FRAME_SIZE)', 'ast_smoother_new(CHANNEL_FRAME_SIZE)')
edit('recv(pvt->sco_socket, pvt->fr.data.ptr, DEVICE_FRAME_SIZE, MSG_DONTWAIT)',
     'recv(pvt->sco_socket, pvt->fr.data.ptr, CHANNEL_FRAME_SIZE, MSG_DONTWAIT)')
edit('\t\t\t\tpvt->sco_socket = -1;\n\t\t\t\tast_smoother_reset',
     '\t\t\t\tpvt->sco_socket = -1;\n\t\t\t\tpvt->sco_tx_size = 0;\n\t\t\t\tast_smoother_reset')
edit('\t\tpvt->fr.datalen = r;\n\t\tpvt->fr.samples = r / 2;', '''		/* The socket carries signed 16-bit PCM, not on-air CVSD bytes. */
		if (r % 2) {
			fr = &ast_null_frame;
			goto e_return;
		}
		sco_observe_packet(pvt, r);
		pvt->fr.datalen = r;
		pvt->fr.samples = r / 2;''')
edit('''	ast_smoother_feed(pvt->bt_out_smoother, frame);

	while ((f = ast_smoother_read(pvt->bt_out_smoother))) {
		sco_write(pvt->sco_socket, f->data.ptr, f->datalen);
	}''', '''	/* In particular for USB, wait for a received host packet. SCO_OPTIONS
	 * is a maximum, and the eSCO event describes the radio payload.
	 */
	if (pvt->sco_socket != -1 && pvt->sco_tx_size) {
		ast_smoother_feed(pvt->bt_out_smoother, frame);
		while ((f = ast_smoother_read(pvt->bt_out_smoother))) {
			sco_write(pvt->sco_socket, f->data.ptr, f->datalen);
		}
	}''')
edit('r = write(s, buf, len);', 'r = send(s, buf, len, MSG_DONTWAIT | MSG_NOSIGNAL);')

helper = '''static uint16_t sco_host_packet_size(unsigned int received, unsigned int mtu)
{
	if (received < 2 || received % 2 || received > CHANNEL_FRAME_SIZE || mtu < 2) {
		return 0;
	}
	return MIN(received, mtu & ~1u);
}

static void sco_observe_packet(struct mbl_pvt *pvt, unsigned int received)
{
	uint16_t size = sco_host_packet_size(received, pvt->sco_mtu);

	if (size != pvt->sco_tx_size) {
		pvt->sco_tx_size = size;
		/* Discard an old partial output packet on a transport size change. */
		ast_smoother_reset(pvt->bt_out_smoother, size ? size : CHANNEL_FRAME_SIZE);
		ast_debug(1, "[%s] SCO host TX size %u, received %u, socket MTU %u\\n",
			pvt->id, (unsigned int)size, received, (unsigned int)pvt->sco_mtu);
	}
}

static void sco_configure_socket(struct mbl_pvt *pvt)
{
	struct sco_options options;
	socklen_t length = sizeof(options);

	pvt->sco_mtu = 0;
	pvt->sco_tx_size = 0;
	ast_smoother_reset(pvt->bt_out_smoother, CHANNEL_FRAME_SIZE);
	ast_smoother_reset(pvt->bt_in_smoother, CHANNEL_FRAME_SIZE);
	if (getsockopt(pvt->sco_socket, SOL_SCO, SCO_OPTIONS, &options, &length)
		|| length != sizeof(options)) {
		ast_log(LOG_WARNING, "[%s] cannot read SCO socket MTU\\n", pvt->id);
		return;
	}
	pvt->sco_mtu = options.mtu;
}

'''
edit('/*!\n * \\brief Accept SCO connections.', helper + '/*!\n * \\brief Accept SCO connections.')
edit('\tsocklen_t len;\n\tchar saddr[18];\n\tstruct sco_options so;', '\tchar saddr[18];')
edit('\tlen = sizeof(so);\n\tgetsockopt(sock, SOL_SCO, SCO_OPTIONS, &so, &len);\n\n', '')
edit('ast_debug(1, "Incoming Audio Connection from device %s MTU is %d\\n", saddr, so.mtu);',
     'ast_debug(1, "Incoming Audio Connection from device %s\\n", saddr);')
edit('if (!bacmp(&pvt->addr, &addr.sco_bdaddr))',
     'if (pvt->adapter == adapter && !bacmp(&pvt->addr, &addr.sco_bdaddr))')
edit('\tpvt->sco_socket = sock;\n', '\tpvt->sco_socket = sock;\n\tsco_configure_socket(pvt);\n')
edit('\t\t\t\t\tast_channel_set_fd(pvt->owner, 0, pvt->sco_socket);',
     '\t\t\t\t\tsco_configure_socket(pvt);\n\t\t\t\t\tast_channel_set_fd(pvt->owner, 0, pvt->sco_socket);')
edit('\t\t\t\tpvt->incoming = 1;\n', '\t\t\t\tsco_configure_socket(pvt);\n\t\t\t\tpvt->incoming = 1;\n')
assert 'DEVICE_FRAME_SIZE' not in s
(root / 'chan_mobile.c').write_text(s)
(root / 'host_framing.inc').write_text(helper)
for name in ('previous', 'recovery'):
    patch = ''.join(difflib.unified_diff((root / (name + '.c')).read_text().splitlines(True), s.splitlines(True),
        fromfile='a/src/addons/chan_mobile.c', tofile='b/src/addons/chan_mobile.c'))
    (root / ('from-' + name + '.patch')).write_text(patch)
