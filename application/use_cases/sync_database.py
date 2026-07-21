from infrastructure.sync.pg_sync_engine import trigger_sync_pg


class SyncDatabaseUseCase:
    def __init__(self, pool=None):
        self._pool = pool

    async def execute(
        self,
        full_sync: bool = False,
        sync_messages: bool = False,
        messages_days: int | None = None,
        year: int | None = None,
        month: int | None = None,
        backfill_surveys: bool = False,
        sync_today: bool = False,
    ):
        pool = self._pool
        if pool is None:
            from api.dependencies import get_pool

            pool = await get_pool()
        return await trigger_sync_pg(
            pool,
            full_sync=full_sync,
            sync_messages=sync_messages,
            messages_days=messages_days,
            year=year,
            month=month,
            backfill_surveys=backfill_surveys,
            sync_today=sync_today,
        )
