from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

# 1. Функция
# Имя отражает суть: назначение сервисов новому пользователю
assign_default_services_function = PGFunction(
    schema="public",
    signature="assign_default_services_function()",
    definition="""
    RETURNS TRIGGER
    AS $$
    BEGIN
        -- Фиксируем search_path для безопасности
        SET search_path = public;

        -- Создаем записи в user_services для нового пользователя со всеми активными сервисами
        INSERT INTO public.user_services (user_id, service_id, config_data)
        SELECT NEW.id, s.id, s.user_default_config_data
        FROM public.services s
        WHERE s.is_active is true
        and s.is_blocked is false;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """,
)

# 2. Триггер
# Имя следует конвенции: trg_<<событие>>_<<таблица>>_<<действие>>
trg_after_insert_users_assign_services = PGTrigger(
    schema="public",
    signature="trg_after_insert_users_assign_services",
    on_entity="public.users",  # Рекомендуется заменить my_table на users
    definition="AFTER INSERT ON public.users FOR EACH ROW EXECUTE FUNCTION public.assign_default_services_function()",
)
