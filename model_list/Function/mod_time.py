from datetime import datetime, timezone, timedelta

def get_iso8601_time_with_ns() -> str:
    dt = datetime.now(timezone(timedelta(hours=-8)))  # 固定 -08:00 时区
    nano_tail = "583"  # 固定纳秒后三位
    formatted = dt.strftime(f"%Y-%m-%dT%H:%M:%S.%f{nano_tail}%z")
    return formatted[:-5] + ":" + formatted[-5:]  # 改 %z 输出为 -08:00 格式