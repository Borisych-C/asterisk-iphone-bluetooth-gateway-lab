static uint16_t sco_host_packet_size(unsigned int received, unsigned int mtu)
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
		ast_debug(1, "[%s] SCO host TX size %u, received %u, socket MTU %u\n",
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
		ast_log(LOG_WARNING, "[%s] cannot read SCO socket MTU\n", pvt->id);
		return;
	}
	pvt->sco_mtu = options.mtu;
}

