import os
from typing import Dict, Optional, Sequence

import fsspec

from src.node.base_node import BaseNode, TextNode
from src.storage.kv_store.simple_kvstore import SimpleKVStore
from src.utils.files import concat_dirs

from .base import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_PERSIST_DIR,
    DEFAULT_PERSIST_FNAME,
    DEFAULT_PERSIST_PATH,
    BaseDocumentStore,
    RefDocInfo
)
from .utils import doc_to_json, json_to_doc

DEFAULT_NAMESPACE = "docstore"

class SimpleDocumentStore(BaseDocumentStore):
    """Simple Document (Node) store.

    An in-memory store for Document and Node objects.

    Args:
        simple_kvstore (SimpleKVStore): simple key-value store
        namespace (str): namespace for the docstore

    """

    def __init__(
        self,
        kvstore: Optional[SimpleKVStore] = None,
        namespace: Optional[str] = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """Init a SimpleDocumentStore."""
        self._kvstore = kvstore or SimpleKVStore()
        self._namespace = namespace or DEFAULT_NAMESPACE
        self._node_collection = f"{self._namespace}/data"
        self._ref_doc_collection = f"{self._namespace}/ref_doc_info"
        self._metadata_collection = f"{self._namespace}/metadata"
        self._batch_size = batch_size

    # ======================== 
    # Store Function 
    # ========================

    @classmethod
    def from_persist_dir(
        cls,
        persist_dir: str = DEFAULT_PERSIST_DIR,
        namespace: Optional[str] = None,
        fs: Optional[fsspec.AbstractFileSystem] = None,
    ) -> "SimpleDocumentStore":
        """Create a SimpleDocumentStore from a persist directory.

        Args:
            persist_dir (str): directory to persist the store
            namespace (Optional[str]): namespace for the docstore
            fs (Optional[fsspec.AbstractFileSystem]): filesystem to use

        """
        if fs is not None:
            persist_path = concat_dirs(persist_dir, DEFAULT_PERSIST_FNAME)
        else:
            persist_path = os.path.join(persist_dir, DEFAULT_PERSIST_FNAME)
        return cls.from_persist_path(persist_path, namespace=namespace, fs=fs)

    @classmethod
    def from_persist_path(
        cls,
        persist_path: str,
        namespace: Optional[str] = None,
        fs: Optional[fsspec.AbstractFileSystem] = None,
    ) -> "SimpleDocumentStore":
        """Create a SimpleDocumentStore from a persist path.

        Args:
            persist_path (str): Path to persist the store
            namespace (Optional[str]): namespace for the docstore
            fs (Optional[fsspec.AbstractFileSystem]): filesystem to use

        """
        simple_kvstore = SimpleKVStore.from_persist_path(persist_path, fs=fs)
        return cls(simple_kvstore, namespace)

    def persist(
        self,
        persist_path: str = DEFAULT_PERSIST_PATH,
        fs: Optional[fsspec.AbstractFileSystem] = None,
    ) -> None:
        """Persist the store."""
        self._kvstore.persist(persist_path, fs=fs)

    @classmethod
    def from_dict(
        cls, save_dict: dict, namespace: Optional[str] = None
    ) -> "SimpleDocumentStore":
        simple_kvstore = SimpleKVStore.from_dict(save_dict)
        return cls(simple_kvstore, namespace)

    def to_dict(self) -> dict:
        assert isinstance(self._kvstore, SimpleKVStore)
        return self._kvstore.to_dict()

    # ======================== 
    # Implement main interface 
    # ========================

    @property
    def docs(self) -> Dict[str, BaseNode]:
        """Get all documents.

        Returns:
            Dict[str, BaseDocument]: documents

        """
        json_dict = self._kvstore.get_all(collection=self._node_collection)
        return {key: json_to_doc(json) for key, json in json_dict.items()}

    def add_documents(
        self,
        nodes: Sequence[BaseNode],
        allow_update: bool = True,
        batch_size: Optional[int] = None,
        store_text: bool = True,
    ) -> None:
        """Add a document to the store.

        Args:
            docs (List[BaseDocument]): documents
            allow_update (bool): allow update of docstore from document

        """
        batch_size = batch_size or self._batch_size
        if batch_size > 1:
            if store_text:
                self._kvstore.put_all(
                    [(node.node_id, doc_to_json(node)) for node in nodes],
                    collection=self._node_collection,
                )
            ref_docs, metadatas = [], []
            for node in nodes:
                metadata = {"doc_hash": node.hash}
                if isinstance(node, TextNode) and node.ref_doc_id is not None:
                    ref_doc_info = (
                        self.get_ref_doc_info(node.ref_doc_id) or RefDocInfo()
                    )
                    if node.node_id not in ref_doc_info.node_ids:
                        ref_doc_info.node_ids.append(node.node_id)
                    if not ref_doc_info.metadata:
                        ref_doc_info.metadata = node.metadata or {}
                    metadata["ref_doc_id"] = node.ref_doc_id
                    ref_docs.append((node.node_id, ref_doc_info.to_dict()))
                metadatas.append((node.node_id, metadata))
            self._kvstore.put_all(
                ref_docs,
                collection=self._ref_doc_collection,
            )
            self._kvstore.put_all(
                metadatas,
                collection=self._metadata_collection,
            )
        else:
            for node in nodes:
                # NOTE: doc could already exist in the store, but we overwrite it
                if not allow_update and self.document_exists(node.node_id):
                    raise ValueError(
                        f"node_id {node.node_id} already exists. "
                        "Set allow_update to True to overwrite."
                    )
                node_key = node.node_id
                data = doc_to_json(node)

                if store_text:
                    self._kvstore.put(node_key, data, collection=self._node_collection)

                # update doc_collection if needed
                metadata = {"doc_hash": node.hash}
                if isinstance(node, TextNode) and node.ref_doc_id is not None:
                    ref_doc_info = (
                        self.get_ref_doc_info(node.ref_doc_id) or RefDocInfo()
                    )
                    if node.node_id not in ref_doc_info.node_ids:
                        ref_doc_info.node_ids.append(node.node_id)
                    if not ref_doc_info.metadata:
                        ref_doc_info.metadata = node.metadata or {}
                    self._kvstore.put(
                        node.ref_doc_id,
                        ref_doc_info.to_dict(),
                        collection=self._ref_doc_collection,
                    )

                    # update metadata with map
                    metadata["ref_doc_id"] = node.ref_doc_id
                    self._kvstore.put(
                        node_key, metadata, collection=self._metadata_collection
                    )
                else:
                    self._kvstore.put(
                        node_key, metadata, collection=self._metadata_collection
                    )

    def get_document(self, doc_id: str, raise_error: bool = True) -> Optional[BaseNode]:
        """Get a document from the store.

        Args:
            doc_id (str): document id
            raise_error (bool): raise error if doc_id not found

        """
        json = self._kvstore.get(doc_id, collection=self._node_collection)
        if json is None:
            if raise_error:
                raise ValueError(f"doc_id {doc_id} not found.")
            else:
                return None
        return json_to_doc(json)

    def get_ref_doc_info(self, ref_doc_id: str) -> Optional[RefDocInfo]:
        """Get the RefDocInfo for a given ref_doc_id."""
        ref_doc_info = self._kvstore.get(
            ref_doc_id, collection=self._ref_doc_collection
        )
        if not ref_doc_info:
            return None

        # TODO: deprecated legacy support
        if "doc_ids" in ref_doc_info:
            ref_doc_info["node_ids"] = ref_doc_info.get("doc_ids", [])
            ref_doc_info.pop("doc_ids")

            ref_doc_info["metadata"] = ref_doc_info.get("extra_info", {})
            ref_doc_info.pop("extra_info")

        return RefDocInfo(**ref_doc_info)

    def get_all_ref_doc_info(self) -> Optional[Dict[str, RefDocInfo]]:
        """Get a mapping of ref_doc_id -> RefDocInfo for all ingested documents."""
        ref_doc_infos = self._kvstore.get_all(collection=self._ref_doc_collection)
        if ref_doc_infos is None:
            return None

        # TODO: deprecated legacy support
        all_ref_doc_infos = {}
        for doc_id, ref_doc_info in ref_doc_infos.items():
            if "doc_ids" in ref_doc_info:
                ref_doc_info["node_ids"] = ref_doc_info.get("doc_ids", [])
                ref_doc_info.pop("doc_ids")

                ref_doc_info["metadata"] = ref_doc_info.get("extra_info", {})
                ref_doc_info.pop("extra_info")
                all_ref_doc_infos[doc_id] = RefDocInfo(**ref_doc_info)

        return all_ref_doc_infos

    def ref_doc_exists(self, ref_doc_id: str) -> bool:
        """Check if a ref_doc_id has been ingested."""
        return self.get_ref_doc_info(ref_doc_id) is not None

    def document_exists(self, doc_id: str) -> bool:
        """Check if document exists."""
        return self._kvstore.get(doc_id, self._node_collection) is not None

    def _remove_ref_doc_node(self, doc_id: str) -> None:
        """Helper function to remove node doc_id from ref_doc_collection."""
        metadata = self._kvstore.get(doc_id, collection=self._metadata_collection)
        if metadata is None:
            return

        ref_doc_id = metadata.get("ref_doc_id", None)

        if ref_doc_id is None:
            return

        ref_doc_info = self._kvstore.get(
            ref_doc_id, collection=self._ref_doc_collection
        )

        if ref_doc_info is not None:
            ref_doc_obj = RefDocInfo(**ref_doc_info)

            ref_doc_obj.node_ids.remove(doc_id)

            # delete ref_doc from collection if it has no more doc_ids
            if len(ref_doc_obj.node_ids) > 0:
                self._kvstore.put(
                    ref_doc_id,
                    ref_doc_obj.to_dict(),
                    collection=self._ref_doc_collection,
                )

            self._kvstore.delete(ref_doc_id, collection=self._metadata_collection)

    def delete_document(
        self, doc_id: str, raise_error: bool = True, remove_ref_doc_node: bool = True
    ) -> None:
        """Delete a document from the store."""
        if remove_ref_doc_node:
            self._remove_ref_doc_node(doc_id)

        delete_success = self._kvstore.delete(doc_id, collection=self._node_collection)
        _ = self._kvstore.delete(doc_id, collection=self._metadata_collection)

        if not delete_success and raise_error:
            raise ValueError(f"doc_id {doc_id} not found.")

    def delete_ref_doc(self, ref_doc_id: str, raise_error: bool = True) -> None:
        """Delete a ref_doc and all it's associated nodes."""
        ref_doc_info = self.get_ref_doc_info(ref_doc_id)
        if ref_doc_info is None:
            if raise_error:
                raise ValueError(f"ref_doc_id {ref_doc_id} not found.")
            else:
                return

        for doc_id in ref_doc_info.node_ids:
            self.delete_document(doc_id, raise_error=False, remove_ref_doc_node=False)

        self._kvstore.delete(ref_doc_id, collection=self._metadata_collection)
        self._kvstore.delete(ref_doc_id, collection=self._ref_doc_collection)

    def set_document_hash(self, doc_id: str, doc_hash: str) -> None:
        """Set the hash for a given doc_id."""
        metadata = {"doc_hash": doc_hash}
        self._kvstore.put(doc_id, metadata, collection=self._metadata_collection)

    def get_document_hash(self, doc_id: str) -> Optional[str]:
        """Get the stored hash for a document, if it exists."""
        metadata = self._kvstore.get(doc_id, collection=self._metadata_collection)
        if metadata is not None:
            return metadata.get("doc_hash", None)
        else:
            return None

    def get_all_document_hashes(self) -> Dict[str, str]:
        """Get the stored hash for all documents."""
        hashes = {}
        for doc_id in self._kvstore.get_all(collection=self._metadata_collection):
            hash = self.get_document_hash(doc_id)
            if hash is not None:
                hashes[hash] = doc_id
        return hashes
