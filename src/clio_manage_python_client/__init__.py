from pathlib import Path
from typing import ClassVar

pkg_dir = Path(__file__).resolve().parent
models_dir = pkg_dir / "models"

if not models_dir.exists():
    from clio_api_model_generator import clio_manage
    print("'models/' directory not found. Generating models...")
    clio_manage.generate_models(output_dir=models_dir, overwrite=False)

from .client import Client
from .utils import (
    RateMonitor,
    build_field_list,
    end_of_the_month,
    save_to_xlsx,
    get_first_id_from_response,
    get_random_id,
)


class Utils:
    RateMonitor = RateMonitor
    build_field_list = staticmethod(build_field_list)
    end_of_the_month = staticmethod(end_of_the_month)
    save_to_xlsx = staticmethod(save_to_xlsx)
    get_first_id_from_response = staticmethod(get_first_id_from_response)
    get_random_id = staticmethod(get_random_id)


class Manage(Client):
    utils: ClassVar[Utils] = Utils()


__all__ = ["Manage"]