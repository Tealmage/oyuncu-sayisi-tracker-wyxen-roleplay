def query_server_with_retry() -> Optional[Dict[str, Any]]:
    """
    Sunucuyu A2S ile sorgular, başarısız olursa retry yapar.

    Returns:
        Dict: Sunucu ve oyuncu bilgileri veya None (başarısız olursa)
    """
    address = (SERVER_IP, SERVER_PORT)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(
                f"Querying {SERVER_IP}:{SERVER_PORT} "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            # Sunucu bilgilerini al
            server_info = a2s.info(
                address,
                timeout=A2S_TIMEOUT
            )

            # Oyuncu listesini al
            try:
                players = a2s.players(
                    address,
                    timeout=A2S_TIMEOUT
                )

                logger.info(
                    f"A2S_PLAYER query successful - "
                    f"returned {len(players)} players"
                )

            except Exception as e:
                logger.warning(
                    f"A2S_PLAYER query failed: {e}"
                )
                players = []

            logger.info(
                f"Server: {server_info.server_name}"
            )

            logger.info(
                f"Map: {server_info.map_name}"
            )

            logger.info(
                f"Players: "
                f"{server_info.player_count}/"
                f"{server_info.max_players}"
            )

            logger.info(
                f"A2S_PLAYER returned: {len(players)} players"
            )

            # Sunucu oyuncu gösteriyor fakat A2S_PLAYER boş dönüyorsa
            if server_info.player_count > 0 and len(players) == 0:
                logger.warning(
                    "SERVER SHOWS PLAYERS BUT "
                    "A2S_PLAYER RETURNED EMPTY!"
                )

                logger.warning(
                    f"Server reports "
                    f"{server_info.player_count} players "
                    f"but A2S_PLAYER query returned 0"
                )

                logger.warning(
                    "This may be caused by server firewall, "
                    "sv_visiblemaxplayers or AntiDDoS protection."
                )

            return {
                "server_info": server_info,
                "players": players,
                "query_time": get_current_time()
            }

        except Exception as e:
            logger.error(
                f"A2S query failed "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}"
            )

            if attempt < MAX_RETRIES:
                logger.info(
                    f"Retrying in {RETRY_DELAY} seconds..."
                )
                time.sleep(RETRY_DELAY)

            else:
                logger.error(
                    "All retry attempts failed"
                )
                return None

    return None
