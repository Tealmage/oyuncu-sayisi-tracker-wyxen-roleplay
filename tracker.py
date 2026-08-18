#!/usr/bin/env python3
"""
Wyxen Roleplay Garry's Mod Server Player Tracker
Bu script sunucuyu A2S protokolü ile sorgular ve oyuncu istatistiklerini takip eder.
"""

import a2s
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import tempfile
import shutil

# Konfigürasyon
SERVER_IP = "185.213.240.239"
SERVER_PORT = 27015
TIMEZONE = "Europe/Istanbul"
DATA_FILE = "data/stats.json"
POLLING_INTERVAL_MINUTES = 5  # Varsayılan polling interval
A2S_TIMEOUT = 5.0  # A2S sorgu timeout (saniye)
MAX_RETRIES = 3  # Maksimum yeniden deneme sayısı
RETRY_DELAY = 2  # Yeniden denemeler arası bekleme (saniye)

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def get_current_time() -> datetime:
    """Mevcut zamanı UTC olarak döndürür."""
    return datetime.utcnow()


def get_week_start(dt: datetime) -> datetime:
    """Verilen tarih için haftanın başlangıcını (Pazartesi 00:00) döndürür."""
    # ISO week date - Pazartesi = 0
    days_since_monday = dt.weekday()
    week_start = dt - timedelta(days=days_since_monday)
    return week_start.replace(hour=0, minute=0, second=0, microsecond=0)


def get_month_start(dt: datetime) -> datetime:
    """Verilen tarih için ayın başlangıcını döndürür."""
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def query_server_with_retry() -> Optional[Dict[str, Any]]:
    """
    Sunucuyu A2S ile sorgular, başarısız olursa retry yapar.
    
    Returns:
        Dict: Sunucu ve oyuncu bilgileri veya None (başarısız olursa)
    """
    address = (SERVER_IP, SERVER_PORT)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Querying {SERVER_IP}:{SERVER_PORT} (attempt {attempt}/{MAX_RETRIES})")
            
            # Sunucu bilgilerini al
            server_info = a2s.info(address, timeout=A2S_TIMEOUT)
            
            # Oyuncu listesini al
            try:
                players = a2s.players(address, timeout=A2S_TIMEOUT)
            except Exception as e:
                logger.warning(f"A2S_PLAYER query failed: {e}")
                players = []
            
            logger.info(f"Server: {server_info.server_name}")
            logger.info(f"Map: {server_info.map_name}")
            logger.info(f"Players: {server_info.player_count}/{server_info.max_players}")
            
            return {
                "server_info": server_info,
                "players": players,
                "query_time": get_current_time()
            }
            
        except Exception as e:
            logger.error(f"A2S query failed (attempt {attempt}/{MAX_RETRIES}): {e}")
            
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("All retry attempts failed")
                return None
    
    return None


def load_stats() -> Dict[str, Any]:
    """
    Mevcut istatistikleri yükler veya yeni bir yapı oluşturur.
    
    Returns:
        Dict: İstatistik verisi
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded existing data from {DATA_FILE}")
                return data
        except Exception as e:
            logger.error(f"Failed to load {DATA_FILE}: {e}")
            logger.info("Creating new data structure")
    
    # Yeni veri yapısı
    return {
        "server": {
            "ip": SERVER_IP,
            "port": SERVER_PORT,
            "name": None,
            "map": None,
            "game": None,
            "online": False,
            "players": None,
            "max_players": None,
            "last_query": None,
            "last_successful_query": None
        },
        "players": {},
        "metadata": {
            "timezone": TIMEZONE,
            "polling_interval_minutes": POLLING_INTERVAL_MINUTES,
            "first_run": get_current_time().isoformat(),
            "total_queries": 0,
            "failed_queries": 0
        },
        "updated_at": get_current_time().isoformat()
    }


def save_stats(data: Dict[str, Any]) -> bool:
    """
    İstatistikleri atomic write ile güvenli şekilde kaydeder.
    
    Args:
        data: Kaydedilecek veri
    
    Returns:
        bool: Başarılı ise True
    """
    try:
        # Klasörü oluştur
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        
        # Atomic write: önce temporary dosyaya yaz, sonra replace et
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            delete=False,
            dir=os.path.dirname(DATA_FILE) or '.',
            suffix='.tmp'
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = tmp_file.name
        
        # Temporary dosyayı asıl dosyayla değiştir
        shutil.move(tmp_path, DATA_FILE)
        logger.info(f"Saved data to {DATA_FILE}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        # Temporary dosyayı temizle
        try:
            if 'tmp_path' in locals():
                os.unlink(tmp_path)
        except:
            pass
        return False


def get_player_identifier(player: Any) -> Optional[str]:
    """
    Oyuncunun benzersiz kimliğini döndürür.
    
    A2S_PLAYER genellikle SteamID vermez. Bu durumda oyuncu adını kullanıyoruz.
    DİKKAT: Bu yöntem %100 güvenilir değildir çünkü:
    - Oyuncular isimlerini değiştirebilir
    - Aynı isimde farklı oyuncular olabilir
    
    Args:
        player: A2S player objesi
    
    Returns:
        str veya None: Oyuncu kimliği
    """
    # A2S_PLAYER'da SteamID alanı genellikle yok veya 0
    # Bazı durumlarda player.steam_id mevcut olabilir
    if hasattr(player, 'steam_id') and player.steam_id and player.steam_id != 0:
        return str(player.steam_id)
    
    # Fallback: Oyuncu adını kullan
    # Bu ideal değil ama A2S'nin sınırlaması
    if hasattr(player, 'name') and player.name:
        return f"name:{player.name}"
    
    return None


def update_player_stats(
    data: Dict[str, Any],
    query_result: Dict[str, Any],
    last_query_time: Optional[datetime]
) -> Dict[str, Any]:
    """
    Oyuncu istatistiklerini günceller.
    
    Args:
        data: Mevcut istatistik verisi
        query_result: A2S sorgu sonucu
        last_query_time: Son başarılı sorgu zamanı
    
    Returns:
        Dict: Güncellenmiş veri
    """
    current_time = query_result["query_time"]
    server_info = query_result["server_info"]
    players = query_result["players"]
    
    # Sunucu bilgilerini güncelle
    data["server"]["name"] = server_info.server_name
    data["server"]["map"] = server_info.map_name
    data["server"]["game"] = server_info.game
    data["server"]["online"] = True
    data["server"]["players"] = server_info.player_count
    data["server"]["max_players"] = server_info.max_players
    data["server"]["last_query"] = current_time.isoformat()
    data["server"]["last_successful_query"] = current_time.isoformat()
    
    # Metadata güncelle
    data["metadata"]["total_queries"] = data["metadata"].get("total_queries", 0) + 1
    
    # Şu anki hafta ve ay başlangıçlarını hesapla
    current_week_start = get_week_start(current_time).isoformat()
    current_month_start = get_month_start(current_time).isoformat()
    
    # Online oyuncuları takip et
    online_player_ids = set()
    
    for player in players:
        player_id = get_player_identifier(player)
        if not player_id:
            continue
        
        online_player_ids.add(player_id)
        player_name = getattr(player, 'name', 'Unknown')
        
        # Yeni oyuncu ise oluştur
        if player_id not in data["players"]:
            data["players"][player_id] = {
                "name": player_name,
                "name_history": [player_name],
                "total_minutes": 0,
                "first_seen": current_time.isoformat(),
                "last_seen": current_time.isoformat(),
                "sessions": [],
                "current_session_start": current_time.isoformat(),
                "weekly_stats": {},
                "monthly_stats": {}
            }
            logger.info(f"New player detected: {player_name}")
        else:
            player_data = data["players"][player_id]
            
            # İsim değişikliğini kontrol et
            if player_data["name"] != player_name:
                if player_name not in player_data.get("name_history", []):
                    player_data["name_history"].append(player_name)
                player_data["name"] = player_name
            
            # Oyuncu daha önce offline ise yeni session başlat
            if "current_session_start" not in player_data or not player_data["current_session_start"]:
                player_data["current_session_start"] = current_time.isoformat()
                logger.info(f"Player reconnected: {player_name}")
            
            player_data["last_seen"] = current_time.isoformat()
    
    # Süre hesaplama: Son başarılı sorgudan bu yana geçen süreyi hesapla
    if last_query_time and (current_time - last_query_time).total_seconds() < 600:  # 10 dakikadan az
        elapsed_minutes = (current_time - last_query_time).total_seconds() / 60.0
        
        for player_id in online_player_ids:
            if player_id in data["players"]:
                player_data = data["players"][player_id]
                
                # Toplam süreyi güncelle
                player_data["total_minutes"] = player_data.get("total_minutes", 0) + elapsed_minutes
                
                # Haftalık istatistik
                if current_week_start not in player_data.get("weekly_stats", {}):
                    player_data["weekly_stats"][current_week_start] = 0
                player_data["weekly_stats"][current_week_start] += elapsed_minutes
                
                # Aylık istatistik
                if current_month_start not in player_data.get("monthly_stats", {}):
                    player_data["monthly_stats"][current_month_start] = 0
                player_data["monthly_stats"][current_month_start] += elapsed_minutes
        
        logger.info(f"Added {elapsed_minutes:.2f} minutes to {len(online_player_ids)} online players")
    
    # Offline olan oyuncuların session'ını kapat
    for player_id, player_data in data["players"].items():
        if player_id not in online_player_ids:
            if "current_session_start" in player_data and player_data["current_session_start"]:
                player_data["current_session_start"] = None
    
    # Eski hafta/ay istatistiklerini temizle (son 12 hafta ve 12 ay tut)
    cleanup_old_stats(data, current_time)
    
    data["updated_at"] = current_time.isoformat()
    
    return data


def cleanup_old_stats(data: Dict[str, Any], current_time: datetime):
    """
    Eski haftalık ve aylık istatistikleri temizler.
    
    Args:
        data: İstatistik verisi
        current_time: Mevcut zaman
    """
    cutoff_week = get_week_start(current_time - timedelta(weeks=12)).isoformat()
    cutoff_month = get_month_start(current_time - timedelta(days=365)).isoformat()
    
    for player_data in data["players"].values():
        # Eski haftalık istatistikleri temizle
        if "weekly_stats" in player_data:
            player_data["weekly_stats"] = {
                k: v for k, v in player_data["weekly_stats"].items()
                if k >= cutoff_week
            }
        
        # Eski aylık istatistikleri temizle
        if "monthly_stats" in player_data:
            player_data["monthly_stats"] = {
                k: v for k, v in player_data["monthly_stats"].items()
                if k >= cutoff_month
            }


def handle_server_offline(data: Dict[str, Any], query_time: datetime) -> Dict[str, Any]:
    """
    Sunucu offline olduğunda veriyi günceller.
    
    Args:
        data: Mevcut veri
        query_time: Sorgu zamanı
    
    Returns:
        Dict: Güncellenmiş veri
    """
    data["server"]["online"] = False
    data["server"]["players"] = None
    data["server"]["last_query"] = query_time.isoformat()
    data["metadata"]["failed_queries"] = data["metadata"].get("failed_queries", 0) + 1
    data["metadata"]["total_queries"] = data["metadata"].get("total_queries", 0) + 1
    
    # Tüm oyuncuların session'ını kapat
    for player_data in data["players"].values():
        if "current_session_start" in player_data:
            player_data["current_session_start"] = None
    
    data["updated_at"] = query_time.isoformat()
    
    logger.warning("Server is offline - no playtime will be added")
    
    return data


def main():
    """Ana fonksiyon."""
    try:
        logger.info("=== Wyxen Player Tracker Started ===")
        
        # Mevcut veriyi yükle
        data = load_stats()
        
        # Son başarılı sorgu zamanını al
        last_query_time = None
        if data["server"]["last_successful_query"]:
            try:
                last_query_time = datetime.fromisoformat(
                    data["server"]["last_successful_query"]
                )
            except:
                pass
        
        # Sunucuyu sorgula
        query_result = query_server_with_retry()
        
        if query_result:
            # Başarılı sorgu - oyuncu istatistiklerini güncelle
            data = update_player_stats(data, query_result, last_query_time)
            logger.info(f"Total tracked players: {len(data['players'])}")
        else:
            # Başarısız sorgu - sunucu offline olarak işaretle
            data = handle_server_offline(data, get_current_time())
        
        # Veriyi kaydet
        if save_stats(data):
            logger.info("=== Tracker Completed Successfully ===")
        else:
            logger.error("=== Tracker Completed with Errors ===")
            exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
