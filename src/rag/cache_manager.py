from typing import Dict, Optional, Any
import json
from datetime import datetime, timedelta
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Gerencia o cache do sistema RAG."""
    
    def __init__(
        self,
        mongodb_uri: str,
        database_name: str = "getai",
        collection_name: str = "cache",
        default_ttl: int = 3600  # 1 hora em segundos
    ):
        """
        Inicializa o gerenciador de cache.
        
        Args:
            mongodb_uri: URI do MongoDB
            database_name: Nome do banco de dados
            collection_name: Nome da coleção
            default_ttl: Tempo padrão de vida do cache em segundos
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.default_ttl = default_ttl
        
        # Criar índices
        self.collection.create_index("key", unique=True)
        self.collection.create_index("expires_at", expireAfterSeconds=0)

    def _generate_key(self, prefix: str, params: Dict) -> str:
        """
        Gera uma chave única para o cache.
        
        Args:
            prefix: Prefixo da chave
            params: Parâmetros para gerar a chave
            
        Returns:
            Chave única
        """
        # Ordena os parâmetros para garantir consistência
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{prefix}:{sorted_params}"

    def get(self, prefix: str, params: Dict) -> Optional[Any]:
        """
        Recupera um item do cache.
        
        Args:
            prefix: Prefixo da chave
            params: Parâmetros da chave
            
        Returns:
            Item do cache ou None se não encontrado
        """
        try:
            key = self._generate_key(prefix, params)
            doc = self.collection.find_one({"key": key})
            
            if doc and doc.get("expires_at") > datetime.utcnow():
                logger.debug(f"Cache hit: {key}")
                return doc["value"]
            
            logger.debug(f"Cache miss: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar do cache: {str(e)}")
            return None

    def set(
        self,
        prefix: str,
        params: Dict,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Armazena um item no cache.
        
        Args:
            prefix: Prefixo da chave
            params: Parâmetros da chave
            value: Valor a ser armazenado
            ttl: Tempo de vida em segundos
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            key = self._generate_key(prefix, params)
            ttl = ttl or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            self.collection.update_one(
                {"key": key},
                {
                    "$set": {
                        "value": value,
                        "expires_at": expires_at,
                        "updated_at": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            logger.debug(f"Cache set: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar no cache: {str(e)}")
            return False

    def delete(self, prefix: str, params: Dict) -> bool:
        """
        Remove um item do cache.
        
        Args:
            prefix: Prefixo da chave
            params: Parâmetros da chave
            
        Returns:
            True se removido com sucesso
        """
        try:
            key = self._generate_key(prefix, params)
            result = self.collection.delete_one({"key": key})
            
            if result.deleted_count > 0:
                logger.debug(f"Cache deleted: {key}")
                return True
                
            logger.debug(f"Cache delete miss: {key}")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover do cache: {str(e)}")
            return False

    def clear(self, prefix: Optional[str] = None) -> bool:
        """
        Limpa o cache.
        
        Args:
            prefix: Se fornecido, limpa apenas itens com este prefixo
            
        Returns:
            True se limpo com sucesso
        """
        try:
            if prefix:
                query = {"key": {"$regex": f"^{prefix}:"}}
            else:
                query = {}
                
            result = self.collection.delete_many(query)
            logger.info(f"Cache cleared: {result.deleted_count} items")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False

    def get_stats(self) -> Dict:
        """
        Retorna estatísticas do cache.
        
        Returns:
            Dicionário com estatísticas
        """
        try:
            total_items = self.collection.count_documents({})
            expired_items = self.collection.count_documents({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            stats = {
                "total_items": total_items,
                "active_items": total_items - expired_items,
                "expired_items": expired_items,
                "default_ttl": self.default_ttl
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            raise
