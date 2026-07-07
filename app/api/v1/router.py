from fastapi import APIRouter

from app.api.v1.endpoints import dataset_files, datasets, validation_rules, validation_runs, validation_errors

router = APIRouter(prefix="/api/v1")

router.include_router(datasets.router)
router.include_router(dataset_files.router)  
router.include_router(validation_rules.router)
router.include_router(validation_runs.router)
router.include_router(validation_errors.router)
router.include_router(validation_runs.run_router) 
