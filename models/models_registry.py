from typing import Dict, Type, Optional, Any
from models.query import *  # Import all query models
from models.request_body import *  # Import all request body models
from models.endpoints import Endpoints as EndpointDefinitions 

class Endpoints:
    """
    Registry for storing endpoint metadata, including paths,
    query models, and request body models.
    """

    registry: Dict[str, Dict[str, Optional[Type]]] = {}
    
    @classmethod
    def list_all_endpoints(cls) -> List[str]:
        """
        List all available endpoints.
        :return: A list of endpoint names.
        """
        return list(cls.registry.keys())

    @classmethod
    def get_endpoint_info(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve detailed metadata about a specific endpoint.
        :param name: The name of the endpoint to retrieve.
        :return: A dictionary with endpoint metadata or None if not found.
        """
        return cls.registry.get(name)
    
    
    @classmethod
    def initialize_registry(cls):
        """
        Dynamically initialize the registry by parsing the `Endpoints` class
        from `models.endpoints`.
        """
        for name, metadata in EndpointDefinitions.registry.items():
            cls.registry[name] = {
                "path": metadata["path"],
                "method": metadata["method"],
                "query_model": metadata.get("query_model"),
                "request_body_model": metadata.get("request_body_model"),
                "field_model": metadata.get("field_model")
            }

    @classmethod
    def get_endpoint(cls, name: str) -> Optional[Dict[str, Type]]:
        """
        Retrieve endpoint metadata by name.

        :param name: The name of the endpoint to retrieve.
        :return: A dictionary containing endpoint metadata or None if not found.
        """
        return cls.registry.get(name)

# Initialize the registry dynamically from the models.endpoints
Endpoints.initialize_registry()
