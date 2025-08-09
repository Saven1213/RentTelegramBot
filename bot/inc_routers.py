from handlers import router as handlers_router
from aiogram import Router

router = Router()

router.include_router(handlers_router)
