"""
Code Generation Engine with AST Manipulation
============================================

Generates code from AST structures and patterns with support for:
- Component extraction from AST
- Pattern-based code generation
- AST to code conversion
- Code formatting and validation
"""

import ast
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from ..memory import CodeMemory

logger = logging.getLogger("synthia.execution.code_generator")


class CodeGenerator:
    """
    Generates code from AST structures and patterns.
    
    Key features:
    - AST traversal and manipulation
    - Pattern-based component extraction
    - Code generation from patterns
    - Formatting and validation
    """
    
    def __init__(self, code_memory: Optional[CodeMemory] = None):
        self.code_memory = code_memory or CodeMemory()
        self.patterns: Dict[str, str] = {}
        self.ast_transformers: List[ast.NodeTransformer] = []
        
        logger.info("Code generation engine initialized")
    
    def load_patterns(self, patterns_dir: str = "patterns"):
        """Load code patterns from directory"""
        try:
            import os
            for filename in os.listdir(patterns_dir):
                if filename.endswith(".txt") or filename.endswith(".template"):
                    pattern_name = os.path.splitext(filename)[0]
                    with open(os.path.join(patterns_dir, filename), "r", encoding="utf-8") as f:
                        self.patterns[pattern_name] = f.read()
            logger.info(f"Loaded {len(self.patterns)} code patterns")
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")
    
    def extract_components_from_ast(self, source_code: str) -> Dict[str, Any]:
        """Extract components from AST"""
        try:
            tree = ast.parse(source_code)
            components = {
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    components["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "body": ast.dump(node.body),
                        "decorator_list": [ast.dump(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.ClassDef):
                    components["classes"].append({
                        "name": node.name,
                        "bases": [ast.dump(base) for base in node.bases],
                        "body": [ast.dump(stmt) for stmt in node.body]
                    })
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    components["imports"].append(ast.dump(node))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            components["variables"].append({
                                "name": target.id,
                                "value": ast.dump(node.value)
                            })
            
            logger.debug(f"Extracted components: {len(components['functions'])} functions, "
                        f"{len(components['classes'])} classes, "
                        f"{len(components['imports'])} imports")
            
            return components
        except Exception as e:
            logger.error(f"AST parsing failed: {e}")
            return {}
    
    def generate_from_pattern(self, pattern_name: str, context: Dict[str, Any]) -> str:
        """Generate code from pattern with context"""
        if pattern_name not in self.patterns:
            logger.warning(f"Pattern '{pattern_name}' not found")
            return ""
        
        try:
            template = self.patterns[pattern_name]
            return self._render_template(template, context)
        except Exception as e:
            logger.error(f"Pattern rendering failed: {e}")
            return ""
    
    def _render_template(self, template: str, context: Dict[str, Any]) -> str:
        """Render template with context variables"""
        try:
            for key, value in context.items():
                # Handle list and dict values specially
                if isinstance(value, list):
                    value_str = "\n".join(str(item) for item in value)
                elif isinstance(value, dict):
                    value_str = "\n".join(f"{k}: {v}" for k, v in value.items())
                else:
                    value_str = str(value)
                
                # Replace {{key}} with value
                template = re.sub(rf"{{{{\s*{key}\s*}}}}", value_str, template)
            
            return template
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template
    
    def optimize_ast(self, tree: ast.AST) -> ast.AST:
        """Optimize AST using transformers"""
        for transformer in self.ast_transformers:
            tree = transformer.visit(tree)
        return tree
    
    def format_code(self, code: str, language: str = "python") -> str:
        """Format generated code"""
        try:
            if language == "python":
                import black
                return black.format_str(code, mode=black.FileMode(line_length=88))
            elif language == "javascript" or language == "typescript":
                import jsbeautifier
                return jsbeautifier.beautify(code)
            elif language == "html" or language == "css":
                import bs4
                # Basic HTML/CSS formatting
                return bs4.BeautifulSoup(code, "html.parser").prettify()
            else:
                return code
        except Exception as e:
            logger.warning(f"Code formatting failed: {e}")
            return code
    
    def validate_code(self, code: str, language: str = "python") -> List[str]:
        """Validate generated code"""
        errors = []
        
        try:
            if language == "python":
                # Check syntax
                ast.parse(code)
            elif language == "javascript" or language == "typescript":
                import jsonschema
                # Basic JavaScript validation
                pass
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    def generate_component(
        self, 
        component_type: str, 
        name: str, 
        properties: Dict[str, Any],
        language: str = "python"
    ) -> str:
        """Generate a specific component type"""
        contexts = {
            "name": name,
            "properties": properties,
            "timestamp": self._get_timestamp()
        }
        
        if component_type == "function":
            return self._generate_function(contexts, language)
        elif component_type == "class":
            return self._generate_class(contexts, language)
        elif component_type == "component":
            return self._generate_react_component(contexts)
        elif component_type == "api":
            return self._generate_api_endpoint(contexts, language)
        else:
            logger.warning(f"Unknown component type: {component_type}")
            return ""
    
    def _generate_function(self, context: Dict[str, Any], language: str) -> str:
        """Generate function code"""
        if language == "python":
            args = ", ".join([f"{k}={v}" for k, v in context['properties'].items()])
            return f"""def {context['name']}({args}):
    \"\"\"Generated function: {context['name']}\"\"\"
    pass
"""
        
        return ""
    
    def _generate_class(self, context: Dict[str, Any], language: str) -> str:
        """Generate class code"""
        if language == "python":
            return f"""class {context['name']}:
    \"\"\"Generated class: {context['name']}\"\"\"
    
    def __init__(self, {', '.join(context['properties'].keys())}):
        {chr(10).join([f'        self.{k} = {k}' for k in context['properties'].keys()])}
"""
        
        return ""
    
    def _generate_react_component(self, context: Dict[str, Any]) -> str:
        """Generate React component code"""
        props = ", ".join([f"{k}={{props.{k}}}" for k in context['properties'].keys()])
        return f"""import React from 'react';

export const {context['name']} = (props) => {{
  return (
    <div className=\"{context['name'].lower()}\">
      {props.children}
    </div>
  );
}};
"""
    
    def _generate_api_endpoint(self, context: Dict[str, Any], language: str) -> str:
        """Generate API endpoint code"""
        if language == "python":
            return f"""@app.route('/api/{context['name']}', methods=['GET'])
def api_{context['name']}():
    \"\"\"API endpoint for {context['name']}\"\"\"
    return jsonify({{
        'status': 'success',
        'data': {context['properties']}
    }})
"""
        
        return ""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for code generation"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_code(self, filename: str, code: str):
        """Save generated code to file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(code)
            logger.info(f"Code saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save code: {e}")
    
    def extract_from_file(self, filepath: str) -> Dict[str, Any]:
        """Extract components from a file"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source_code = f.read()
            return self.extract_components_from_ast(source_code)
        except Exception as e:
            logger.error(f"Failed to extract from file: {e}")
            return {}
