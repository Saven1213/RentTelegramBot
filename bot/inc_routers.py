from bot.handlers.handlers import router as all_handlers_router
from aiogram import Router
from bot.handlers.admin_menu import router as admin_router
from bot.handlers.rent_bike import router as rent_bike_router
from bot.handlers.profile import router as profile_router
from bot.handlers.notifies import router as notifies_router
main_router = Router()

main_router.include_router(all_handlers_router)
main_router.include_router(admin_router)
main_router.include_router(rent_bike_router)
main_router.include_router(profile_router)
main_router.include_router(notifies_router)