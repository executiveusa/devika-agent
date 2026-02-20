#!/usr/bin/env python3
"""
SYNTHIA Skill Manager CLI

Command-line interface for managing skills in the SYNTHIA ecosystem.
Provides commands for searching, installing, syncing, and managing skills
across multiple AI tools.

Usage:
    python skill_cli.py search <query>
    python skill_cli.py install <skill_id> [--source skillhub|clawhub|local]
    python skill_cli.py sync <skill_name> [--tools claude,cursor,...]
    python skill_cli.py list
    python skill_cli.py report
    python skill_cli.py uninstall <skill_name>
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.synthia.skill_manager import (
    SkillManager,
    SkillSource,
    SkillScope,
    get_skill_manager,
)
from src.synthia.n8n_integration import get_n8n_integration


def cmd_search(args):
    """Search for skills across sources."""
    sm = get_skill_manager()
    
    # Determine sources
    sources = None
    if args.source:
        source_map = {
            "skillsmp": SkillSource.SKILLSMP,
            "skillhub": SkillSource.SKILLHUB,
            "clawhub": SkillSource.CLAWHUB,
            "local": SkillSource.LOCAL,
        }
        sources = [source_map.get(s) for s in args.source.split(",") if s in source_map]
    
    results = sm.search(args.query, sources=sources, limit=args.limit)
    
    if not results:
        print("No skills found.")
        return
    
    print(f"\nFound {len(results)} skills:\n")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.name}")
        print(f"   Source: {result.source.value}")
        print(f"   Description: {result.description[:100]}...")
        if result.url:
            print(f"   URL: {result.url}")
        print()


def cmd_install(args):
    """Install a skill."""
    sm = get_skill_manager()
    
    # Determine source
    source_map = {
        "skillsmp": SkillSource.SKILLSMP,
        "skillhub": SkillSource.SKILLHUB,
        "clawhub": SkillSource.CLAWHUB,
        "local": SkillSource.LOCAL,
    }
    source = source_map.get(args.source, SkillSource.SKILLHUB)
    
    # Determine scope
    scope = SkillScope.GLOBAL if args.global_scope else SkillScope.PROJECT
    
    # Determine target tools
    target_tools = args.tools.split(",") if args.tools else None
    
    print(f"Installing skill '{args.skill_id}' from {source.value}...")
    
    result = sm.install(
        skill_id=args.skill_id,
        source=source,
        scope=scope,
        target_tools=target_tools,
        skip_security_scan=args.skip_scan,
    )
    
    if result["success"]:
        print(f"\n✓ Successfully installed '{result['skill']['name']}'")
        print("\nInstalled to:")
        for target in result["installed_to"]:
            print(f"  - {target['tool']}: {target['path']}")
    else:
        print(f"\n✗ Installation failed:")
        for error in result["errors"]:
            print(f"  - {error}")
        
        if result["security_findings"]:
            print("\nSecurity findings:")
            for level, findings in result["security_findings"].items():
                if findings and level != "passed":
                    print(f"  {level.upper()}:")
                    for finding in findings:
                        print(f"    - {finding['description']}")


def cmd_sync(args):
    """Sync a skill across tools."""
    sm = get_skill_manager()
    
    target_tools = args.tools.split(",") if args.tools else None
    
    print(f"Syncing skill '{args.skill_name}'...")
    
    result = sm.sync(args.skill_name, target_tools=target_tools)
    
    if result["success"]:
        print(f"\n✓ Successfully synced '{args.skill_name}'")
        print("\nSynced to:")
        for target in result["synced_to"]:
            print(f"  - {target['tool']}: {target['path']}")
    else:
        print(f"\n✗ Sync failed:")
        for error in result["errors"]:
            print(f"  - {error}")


def cmd_list(args):
    """List installed skills."""
    sm = get_skill_manager()
    
    skills = sm.list_installed()
    
    if not skills:
        print("No skills installed.")
        return
    
    print(f"\nInstalled skills ({len(skills)}):\n")
    for skill in skills:
        print(f"  • {skill['name']} (v{skill['version']})")
        print(f"    Source: {skill['source']}")
        print(f"    Path: {skill['path']}")
        print()


def cmd_report(args):
    """Generate skill report."""
    sm = get_skill_manager()
    
    report = sm.generate_report()
    
    print("\n" + "=" * 60)
    print("SYNTHIA SKILL REPORT")
    print("=" * 60)
    
    print(f"\nGenerated: {report['generated_at']}")
    print(f"Total skills: {report['summary']['total_skills']}")
    print(f"Tools detected: {report['summary']['tools_detected']}")
    
    print("\n--- Skills by Tool ---\n")
    for tool, data in report["tools"].items():
        print(f"{tool}: {data['count']} skills")
        for skill in data["skills"]:
            print(f"  - {skill['name']} ({skill['scope']})")
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2))
        print(f"\nReport saved to: {output_path}")


def cmd_uninstall(args):
    """Uninstall a skill."""
    sm = get_skill_manager()
    
    print(f"Uninstalling skill '{args.skill_name}'...")
    
    result = sm.uninstall(args.skill_name, remove_from_all_tools=args.all_tools)
    
    if result["success"]:
        print(f"\n✓ Successfully uninstalled '{args.skill_name}'")
        print("\nRemoved from:")
        for target in result["removed_from"]:
            print(f"  - {target['tool']} ({target['scope']}): {target['path']}")
    else:
        print(f"\n✗ Uninstall failed:")
        for error in result["errors"]:
            print(f"  - {error}")


def cmd_n8n(args):
    """n8n workflow commands."""
    n8n = get_n8n_integration()
    
    if args.n8n_action == "list":
        workflows = n8n.list_workflows()
        print(f"\nn8n Workflows ({len(workflows)}):\n")
        for wf in workflows:
            print(f"  • {wf['name']} ({len(wf['nodes'])} nodes)")
            print(f"    ID: {wf['id']}")
            print()
    
    elif args.n8n_action == "convert":
        skill_dir = n8n.convert_to_workflow(args.workflow_id, Path(args.output_dir or "skills"))
        if skill_dir:
            print(f"✓ Converted workflow to skill: {skill_dir}")
        else:
            print("✗ Failed to convert workflow")
    
    elif args.n8n_action == "search":
        workflows = n8n.search_workflows(args.query)
        print(f"\nFound {len(workflows)} workflows:\n")
        for wf in workflows:
            print(f"  • {wf.name}")
            print(f"    ID: {wf.id}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="SYNTHIA Skill Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for skills")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--source", help="Comma-separated sources (skillsmp,skillhub,clawhub,local)")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")
    search_parser.set_defaults(func=cmd_search)
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("skill_id", help="Skill ID to install")
    install_parser.add_argument("--source", default="skillhub", help="Skill source")
    install_parser.add_argument("--global", dest="global_scope", action="store_true", help="Install globally")
    install_parser.add_argument("--tools", help="Comma-separated target tools")
    install_parser.add_argument("--skip-scan", action="store_true", help="Skip security scan")
    install_parser.set_defaults(func=cmd_install)
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync a skill across tools")
    sync_parser.add_argument("skill_name", help="Skill name to sync")
    sync_parser.add_argument("--tools", help="Comma-separated target tools")
    sync_parser.set_defaults(func=cmd_sync)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List installed skills")
    list_parser.set_defaults(func=cmd_list)
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate skill report")
    report_parser.add_argument("--output", help="Output file path")
    report_parser.set_defaults(func=cmd_report)
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill")
    uninstall_parser.add_argument("skill_name", help="Skill name to uninstall")
    uninstall_parser.add_argument("--all-tools", action="store_true", help="Remove from all tools")
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
    # n8n command
    n8n_parser = subparsers.add_parser("n8n", help="n8n workflow commands")
    n8n_parser.add_argument("n8n_action", choices=["list", "convert", "search"], help="n8n action")
    n8n_parser.add_argument("--workflow-id", help="Workflow ID for conversion")
    n8n_parser.add_argument("--query", help="Search query")
    n8n_parser.add_argument("--output-dir", help="Output directory for converted skills")
    n8n_parser.set_defaults(func=cmd_n8n)
    
    args = parser.parse_args()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
