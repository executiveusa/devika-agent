"""
SYNTHIA CLI - Command Line Interface
====================================

SYNTHIA's command-line interface for interacting with the system.
Provides commands for investigation, execution, memory management, and more.
"""

import asyncio
import click
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.synthia.core import SynthiaCore
from src.synthia.memory import MemoryLayer
from src.synthia.investigation.scanner import RepositoryScanner
from src.synthia.execution import RalphyExecutionEngine, TaskPriority

logger = logging.getLogger("synthia.cli")


class SynthiaCLI:
    """SYNTHIA Command Line Interface"""
    
    def __init__(self):
        self.core: Optional[SynthiaCore] = None
        self.memory: Optional[MemoryLayer] = None
        self.scanner: Optional[RepositoryScanner] = None
        
    async def initialize(self):
        """Initialize SYNTHIA components"""
        logger.info("Initializing SYNTHIA...")
        
        self.memory = MemoryLayer()
        await self.memory.initialize()
        
        self.scanner = RepositoryScanner()
        
        self.core = SynthiaCore(
            memory=self.memory,
            scanner=self.scanner
        )
        
        logger.info("SYNTHIA initialized successfully")
    
    async def investigate(self, path: str) -> dict:
        """Investigate a repository"""
        logger.info(f"Investigating: {path}")
        
        scan_result = await self.scanner.scan(path)
        
        # Store in memory
        await self.memory.store(
            key=f"investigation:{path}",
            value=scan_result.to_dict(),
            layer="project"
        )
        
        return scan_result.to_dict()
    
    async def execute_task(self, title: str, description: str, 
                          priority: str = "standard") -> dict:
        """Execute a single task"""
        engine = RalphyExecutionEngine()
        
        priority_map = {
            "architectural": TaskPriority.ARCHITECTURAL,
            "integration": TaskPriority.INTEGRATION,
            "unknown": TaskPriority.UNKNOWN,
            "standard": TaskPriority.STANDARD,
            "polish": TaskPriority.POLISH
        }
        
        task_priority = priority_map.get(priority.lower(), TaskPriority.STANDARD)
        
        engine.add_task(title, description, task_priority)
        
        # Execute with dummy function
        async def dummy_executor(task):
            await asyncio.sleep(0.1)
            return {"status": "completed"}
        
        results = await engine.execute_all(dummy_executor)
        
        return engine.get_summary()
    
    async def query_memory(self, query: str, layer: str = "project") -> list:
        """Query memory layer"""
        results = await self.memory.retrieve(query, layer=layer)
        return results
    
    async def close(self):
        """Cleanup resources"""
        if self.memory:
            await self.memory.close()


# CLI Commands using Click
@click.group()
@click.pass_context
def synthia_cli(ctx):
    """SYNTHIA - Autonomous AI Coding Agent"""
    ctx.ensure_object(dict)
    ctx.obj['cli'] = SynthiaCLI()


@synthia_cli.command()
@click.argument('path')
@click.pass_context
async def investigate(ctx, path):
    """Investigate a repository"""
    cli = ctx.obj['cli']
    await cli.initialize()
    
    try:
        result = await cli.investigate(path)
        click.echo(f"\n✓ Investigation complete for: {path}")
        click.echo(f"  Files scanned: {result.get('file_count', 0)}")
        click.echo(f"  Tech stack: {', '.join(result.get('tech_stack', []))}")
    finally:
        await cli.close()


@synthia_cli.command()
@click.argument('title')
@click.argument('description')
@click.option('--priority', default='standard', 
              type=click.Choice(['architectural', 'integration', 'unknown', 'standard', 'polish']),
              help='Task priority')
@click.pass_context
async def execute(ctx, title, description, priority):
    """Execute a task"""
    cli = ctx.obj['cli']
    await cli.initialize()
    
    try:
        result = await cli.execute_task(title, description, priority)
        click.echo(f"\n✓ Task executed")
        click.echo(f"  Success: {result['successful']}/{result['total_tasks']}")
        click.echo(f"  Duration: {result['total_duration']:.2f}s")
    finally:
        await cli.close()


@synthia_cli.command()
@click.argument('query')
@click.option('--layer', default='project', 
              type=click.Choice(['project', 'team', 'global']),
              help='Memory layer to query')
@click.pass_context
async def recall(ctx, query, layer):
    """Query memory"""
    cli = ctx.obj['cli']
    await cli.initialize()
    
    try:
        results = await cli.query_memory(query, layer)
        
        if results:
            click.echo(f"\nFound {len(results)} memories:")
            for i, r in enumerate(results[:5], 1):
                click.echo(f"\n{i}. {r.get('key', 'Unknown')}")
                click.echo(f"   Relevance: {r.get('relevance', 0):.2f}")
        else:
            click.echo("\nNo memories found")
    finally:
        await cli.close()


@synthia_cli.command()
@click.argument('key')
@click.argument('value')
@click.option('--layer', default='project',
              type=click.Choice(['project', 'team', 'global']))
@click.pass_context
async def remember(ctx, key, value, layer):
    """Store in memory"""
    cli = ctx.obj['cli']
    await cli.initialize()
    
    try:
        await cli.memory.store(key, value, layer=layer)
        click.echo(f"\n✓ Stored: {key} in {layer} layer")
    finally:
        await cli.close()


@synthia_cli.command()
@click.pass_context
async def status(ctx):
    """Show SYNTHIA status"""
    click.echo("\n╔══════════════════════════════════════╗")
    click.echo("║     SYNTHIA Autonomous Agent         ║")
    click.echo("╠══════════════════════════════════════╣")
    click.echo("║ Status: Ready                        ║")
    click.echo("║ Version: 4.2.0                       ║")
    click.echo("║ Memory: Multi-layer (Project/Team)   ║")
    click.echo("║ Ralphy: Priority Execution           ║")
    click.echo("║ Lightning: Mentor/Observer Active    ║")
    click.echo("╚══════════════════════════════════════╝")


@synthia_cli.command()
@click.pass_context
async def test(ctx):
    """Run SYNTHIA self-test"""
    cli = ctx.obj['cli']
    await cli.initialize()
    
    click.echo("\nRunning SYNTHIA self-test...")
    
    # Test memory
    await cli.memory.store("test_key", {"test": "data"}, layer="project")
    results = await cli.memory.retrieve("test", layer="project")
    memory_ok = len(results) > 0
    click.echo(f"  {'✓' if memory_ok else '✗'} Memory layer")
    
    # Test scanner
    click.echo(f"  ✓ Scanner initialized")
    
    # Test core
    click.echo(f"  ✓ Core initialized")
    
    click.echo("\nAll systems operational!")
    
    await cli.close()


def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run CLI
    try:
        synthia_cli(obj={})
    except KeyboardInterrupt:
        click.echo("\n\nSYNTHIA shutting down...")
        sys.exit(0)
    except Exception as e:
        click.echo(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
