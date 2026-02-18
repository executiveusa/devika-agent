"""
SYNTHIA Memory Manager
======================
Multi-layer persistent memory system inspired by ByteRover.

Memory Layers:
- PROJECT: Local to current project, stored in project directory
- TEAM: Shared across team members, stored in shared location
- GLOBAL: Universal patterns and knowledge, synced to Archon X

Features:
- Vector search for semantic retrieval
- Git-like version control for memories
- Automatic knowledge extraction
- Cross-session persistence
"""

import os
import json
import sqlite3
import hashlib
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime
from pathlib import Path
import threading
import pickle


class MemoryLayer(Enum):
    """Memory layer hierarchy"""
    PROJECT = "project"      # Local to project
    TEAM = "team"            # Shared across team
    GLOBAL = "global"        # Universal patterns


@dataclass
class MemoryEntry:
    """A single memory entry"""
    key: str
    value: Any
    layer: MemoryLayer
    project_name: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "key": self.key,
            "value": self.value,
            "layer": self.layer.value,
            "project_name": self.project_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata
        }


@dataclass
class SearchResult:
    """Result of a memory search"""
    entry: MemoryEntry
    score: float
    highlights: List[str] = field(default_factory=list)


class MemoryManager:
    """
    Multi-layer memory management system.
    
    Provides persistent storage with semantic search capabilities.
    All memories are automatically synced to Archon X for team sharing.
    
    Usage:
        memory = MemoryManager()
        
        # Store a memory
        memory.store(
            key="pattern:auth-flow",
            value={"steps": ["login", "verify", "session"]},
            layer=MemoryLayer.PROJECT,
            project_name="my-app"
        )
        
        # Search memories
        results = memory.search(
            query="authentication",
            layer=MemoryLayer.PROJECT,
            limit=5
        )
    """
    
    def __init__(
        self,
        backend: str = "sqlite",
        db_path: Optional[str] = None,
        enable_embeddings: bool = True,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        self.backend = backend
        self.enable_embeddings = enable_embeddings
        self.embedding_model = embedding_model
        self._lock = threading.Lock()
        
        # Initialize storage
        if backend == "sqlite":
            self.db_path = db_path or self._get_default_db_path()
            self._init_sqlite()
        elif backend == "memory":
            self._memory_store: Dict[str, MemoryEntry] = {}
        
        # Initialize embedding model if enabled
        self._embedder = None
        if enable_embeddings:
            self._init_embedder()
    
    def _get_default_db_path(self) -> str:
        """Get default database path based on OS"""
        base_dir = os.getenv("SYNTHIA_DATA_DIR")
        if not base_dir:
            # Use project data directory
            base_dir = os.path.join(os.getcwd(), "data", "synthia_memory")
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, "memory.db")
    
    def _init_sqlite(self):
        """Initialize SQLite database with FTS5 for full-text search"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                layer TEXT NOT NULL,
                project_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                key,
                value,
                tags,
                content='memories',
                content_rowid='rowid'
            )
        """)
        
        # Embeddings table for vector search
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                key TEXT PRIMARY KEY,
                embedding BLOB,
                FOREIGN KEY (key) REFERENCES memories(key)
            )
        """)
        
        # Version history for git-like versioning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                version INTEGER NOT NULL,
                changed_at TEXT NOT NULL,
                change_type TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_layer 
            ON memories(layer)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_project 
            ON memories(project_name)
        """)
        
        conn.commit()
        conn.close()
    
    def _init_embedder(self):
        """Initialize embedding model for semantic search"""
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer(self.embedding_model)
        except ImportError:
            print("Warning: sentence-transformers not installed. Embeddings disabled.")
            self.enable_embeddings = False
        except Exception as e:
            print(f"Warning: Failed to initialize embedder: {e}. Embeddings disabled.")
            self.enable_embeddings = False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self._embedder or not self.enable_embeddings:
            return None
        try:
            return self._embedder.encode(text).tolist()
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return None
    
    def store(
        self,
        key: str,
        value: Any,
        layer: MemoryLayer,
        project_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Store a memory entry.
        
        Args:
            key: Unique identifier for the memory
            value: The value to store (will be JSON serialized)
            layer: Memory layer (PROJECT, TEAM, GLOBAL)
            project_name: Project name for PROJECT layer
            tags: Optional tags for categorization
            metadata: Optional metadata dictionary
            
        Returns:
            True if stored successfully
        """
        with self._lock:
            # Serialize value
            value_str = json.dumps(value) if not isinstance(value, str) else value
            tags_str = json.dumps(tags or [])
            metadata_str = json.dumps(metadata or {})
            now = datetime.utcnow().isoformat()
            
            if self.backend == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Check if exists
                cursor.execute("SELECT version FROM memories WHERE key = ?", (key,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    version = existing[0] + 1
                    cursor.execute("""
                        UPDATE memories 
                        SET value = ?, updated_at = ?, version = ?, tags = ?, metadata = ?
                        WHERE key = ?
                    """, (value_str, now, version, tags_str, metadata_str, key))
                    
                    # Record history
                    cursor.execute("""
                        INSERT INTO memory_history (key, value, version, changed_at, change_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (key, value_str, version, now, "update"))
                else:
                    # Insert new
                    version = 1
                    cursor.execute("""
                        INSERT INTO memories (key, value, layer, project_name, created_at, updated_at, version, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (key, value_str, layer.value, project_name, now, now, version, tags_str, metadata_str))
                    
                    # Record history
                    cursor.execute("""
                        INSERT INTO memory_history (key, value, version, changed_at, change_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (key, value_str, version, now, "create"))
                
                # Update FTS index
                cursor.execute("""
                    INSERT INTO memories_fts (key, value, tags)
                    VALUES (?, ?, ?)
                """, (key, value_str, " ".join(tags or [])))
                
                # Store embedding if enabled
                if self.enable_embeddings:
                    embedding = self._generate_embedding(value_str)
                    if embedding:
                        embedding_blob = pickle.dumps(embedding)
                        cursor.execute("""
                            INSERT OR REPLACE INTO embeddings (key, embedding)
                            VALUES (?, ?)
                        """, (key, embedding_blob))
                
                conn.commit()
                conn.close()
            
            elif self.backend == "memory":
                entry = MemoryEntry(
                    key=key,
                    value=value,
                    layer=layer,
                    project_name=project_name,
                    tags=tags or [],
                    metadata=metadata or {}
                )
                self._memory_store[key] = entry
            
            return True
    
    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory by key"""
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value, layer, project_name, created_at, updated_at, version, tags, metadata
                FROM memories WHERE key = ?
            """, (key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return MemoryEntry(
                    key=row[0],
                    value=json.loads(row[1]) if row[1].startswith("{") or row[1].startswith("[") else row[1],
                    layer=MemoryLayer(row[2]),
                    project_name=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    version=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                    metadata=json.loads(row[8]) if row[8] else {}
                )
        
        elif self.backend == "memory":
            return self._memory_store.get(key)
        
        return None
    
    def search(
        self,
        query: str,
        layer: Optional[MemoryLayer] = None,
        project_name: Optional[str] = None,
        limit: int = 10,
        use_semantic: bool = True
    ) -> List[SearchResult]:
        """
        Search memories by query.
        
        Uses hybrid search:
        - Full-text search for keyword matching
        - Semantic search for meaning-based retrieval
        
        Args:
            query: Search query
            layer: Optional layer filter
            project_name: Optional project filter
            limit: Maximum results to return
            use_semantic: Whether to use semantic search
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query conditions
            conditions = []
            params = []
            
            if layer:
                conditions.append("layer = ?")
                params.append(layer.value)
            if project_name:
                conditions.append("project_name = ?")
                params.append(project_name)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Full-text search
            fts_query = f"""
                SELECT m.key, m.value, m.layer, m.project_name, m.created_at, m.updated_at, m.version, m.tags, m.metadata,
                       bm25(memories_fts) as score
                FROM memories m
                JOIN memories_fts fts ON m.key = fts.key
                WHERE memories_fts MATCH ? AND {where_clause}
                ORDER BY score
                LIMIT ?
            """
            
            try:
                cursor.execute(fts_query, [query] + params + [limit])
                rows = cursor.fetchall()
                
                for row in rows:
                    entry = MemoryEntry(
                        key=row[0],
                        value=json.loads(row[1]) if row[1].startswith("{") or row[1].startswith("[") else row[1],
                        layer=MemoryLayer(row[2]),
                        project_name=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                        version=row[6],
                        tags=json.loads(row[7]) if row[7] else [],
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    results.append(SearchResult(
                        entry=entry,
                        score=abs(row[9]) if row[9] else 0.0
                    ))
            except Exception as e:
                # Fallback to LIKE search if FTS fails
                like_query = f"""
                    SELECT key, value, layer, project_name, created_at, updated_at, version, tags, metadata
                    FROM memories
                    WHERE value LIKE ? AND {where_clause}
                    LIMIT ?
                """
                cursor.execute(like_query, [f"%{query}%"] + params + [limit])
                rows = cursor.fetchall()
                
                for row in rows:
                    entry = MemoryEntry(
                        key=row[0],
                        value=json.loads(row[1]) if row[1].startswith("{") or row[1].startswith("[") else row[1],
                        layer=MemoryLayer(row[2]),
                        project_name=row[3],
                        created_at=row[4],
                        updated_at=row[5],
                        version=row[6],
                        tags=json.loads(row[7]) if row[7] else [],
                        metadata=json.loads(row[8]) if row[8] else {}
                    )
                    results.append(SearchResult(entry=entry, score=0.5))
            
            # Semantic search if enabled and not enough results
            if use_semantic and self.enable_embeddings and len(results) < limit:
                query_embedding = self._generate_embedding(query)
                if query_embedding:
                    semantic_results = self._semantic_search(
                        query_embedding=query_embedding,
                        layer=layer,
                        project_name=project_name,
                        limit=limit - len(results)
                    )
                    # Merge results, avoiding duplicates
                    existing_keys = {r.entry.key for r in results}
                    for sr in semantic_results:
                        if sr.entry.key not in existing_keys:
                            results.append(sr)
            
            conn.close()
        
        elif self.backend == "memory":
            # Simple in-memory search
            for entry in self._memory_store.values():
                if layer and entry.layer != layer:
                    continue
                if project_name and entry.project_name != project_name:
                    continue
                if query.lower() in str(entry.value).lower():
                    results.append(SearchResult(entry=entry, score=0.5))
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    def _semantic_search(
        self,
        query_embedding: List[float],
        layer: Optional[MemoryLayer] = None,
        project_name: Optional[str] = None,
        limit: int = 10
    ) -> List[SearchResult]:
        """Perform semantic search using embeddings"""
        results = []
        
        if self.backend != "sqlite":
            return results
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build conditions
        conditions = []
        params = []
        
        if layer:
            conditions.append("layer = ?")
            params.append(layer.value)
        if project_name:
            conditions.append("project_name = ?")
            params.append(project_name)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # Get all embeddings
        cursor.execute(f"""
            SELECT m.key, m.value, m.layer, m.project_name, m.created_at, m.updated_at, m.version, m.tags, m.metadata, e.embedding
            FROM memories m
            JOIN embeddings e ON m.key = e.key
            WHERE {where_clause}
        """, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        # Calculate cosine similarity
        scored_entries = []
        for row in rows:
            try:
                stored_embedding = pickle.loads(row[9])
                similarity = self._cosine_similarity(query_embedding, stored_embedding)
                
                entry = MemoryEntry(
                    key=row[0],
                    value=json.loads(row[1]) if row[1].startswith("{") or row[1].startswith("[") else row[1],
                    layer=MemoryLayer(row[2]),
                    project_name=row[3],
                    created_at=row[4],
                    updated_at=row[5],
                    version=row[6],
                    tags=json.loads(row[7]) if row[7] else [],
                    metadata=json.loads(row[8]) if row[8] else {}
                )
                scored_entries.append((entry, similarity))
            except Exception:
                continue
        
        # Sort by similarity
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        for entry, score in scored_entries[:limit]:
            results.append(SearchResult(entry=entry, score=score))
        
        return results
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    def delete(self, key: str) -> bool:
        """Delete a memory entry"""
        with self._lock:
            if self.backend == "sqlite":
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Record deletion in history
                cursor.execute("SELECT value, version FROM memories WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row:
                    cursor.execute("""
                        INSERT INTO memory_history (key, value, version, changed_at, change_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (key, row[0], row[1], datetime.utcnow().isoformat(), "delete"))
                
                # Delete from all tables
                cursor.execute("DELETE FROM memories WHERE key = ?", (key,))
                cursor.execute("DELETE FROM embeddings WHERE key = ?", (key,))
                
                conn.commit()
                conn.close()
                return True
            
            elif self.backend == "memory":
                if key in self._memory_store:
                    del self._memory_store[key]
                    return True
        
        return False
    
    def get_history(self, key: str, limit: int = 10) -> List[Dict]:
        """Get version history for a memory entry"""
        if self.backend != "sqlite":
            return []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT key, value, version, changed_at, change_type
            FROM memory_history
            WHERE key = ?
            ORDER BY version DESC
            LIMIT ?
        """, (key, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "key": row[0],
                "value": row[1],
                "version": row[2],
                "changed_at": row[3],
                "change_type": row[4]
            }
            for row in rows
        ]
    
    def export_layer(self, layer: MemoryLayer) -> Dict:
        """Export all memories in a layer for Archon X sync"""
        if self.backend == "sqlite":
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT key, value, project_name, created_at, updated_at, version, tags, metadata
                FROM memories WHERE layer = ?
            """, (layer.value,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return {
                "layer": layer.value,
                "entries": [
                    {
                        "key": row[0],
                        "value": row[1],
                        "project_name": row[2],
                        "created_at": row[3],
                        "updated_at": row[4],
                        "version": row[5],
                        "tags": row[6],
                        "metadata": row[7]
                    }
                    for row in rows
                ]
            }
        
        return {"layer": layer.value, "entries": []}
    
    def import_layer(self, data: Dict) -> int:
        """Import memories from Archon X sync"""
        count = 0
        layer = MemoryLayer(data.get("layer", "global"))
        
        for entry in data.get("entries", []):
            try:
                self.store(
                    key=entry["key"],
                    value=json.loads(entry["value"]) if entry["value"].startswith("{") else entry["value"],
                    layer=layer,
                    project_name=entry.get("project_name"),
                    tags=json.loads(entry.get("tags", "[]")),
                    metadata=json.loads(entry.get("metadata", "{}"))
                )
                count += 1
            except Exception as e:
                print(f"Failed to import entry {entry.get('key')}: {e}")
        
        return count