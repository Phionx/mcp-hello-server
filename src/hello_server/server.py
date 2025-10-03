"""
🔬 Dimensional Analysis & Equation Sanity Checker MCP Server
To run your server, use "uv run dev"
To test interactively, use "uv run playground"

This server provides tools for:
- Checking dimensional consistency of physics equations
- Listing available physical units and constants
- Validating equation syntax and units

🧑‍💻 MCP's Python SDK (helps you define your server)
https://github.com/modelcontextprotocol/python-sdk
"""

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field
from pint import UnitRegistry
from typing import Dict, Any, Optional

from smithery.decorators import smithery


# Optional: If you want to receive session-level config from user, define it here
class ConfigSchema(BaseModel):
    # access_token: str = Field(..., description="Your access token for authentication")
    verbose_output: bool = Field(False, description="Show detailed unit analysis in results")
    include_constants: bool = Field(True, description="Include physical constants in unit listings")
    custom_variables: Optional[str] = Field(None, description="Custom variables in format 'var1=unit1,var2=unit2' (e.g., 'g=9.81*meter/second**2,A=meter**2')")


# For servers with configuration:
@smithery.server(config_schema=ConfigSchema)
# For servers without configuration, simply use:
# @smithery.server()
def create_server():
    """Create and configure the MCP server."""

    # Create your FastMCP server as usual
    server = FastMCP("Dimensional Analysis Server")

    # Initialize unit registry and context
    ureg = UnitRegistry()
    Q_ = ureg.Quantity

    def build_context(session_config: ConfigSchema) -> Dict[str, Any]:
        """Build the context dictionary with base units and custom variables."""
        # Define base symbols with units (dimensional placeholders)
        base_context = {
        # Mechanics
        "F": Q_(1, "newton"),                 # Force
        "m": Q_(1, "kilogram"),               # Mass
        "a": Q_(1, "meter/second**2"),        # Acceleration
        "v": Q_(1, "meter/second"),           # Velocity
        "u": Q_(1, "meter/second"),           # Initial velocity
        "d": Q_(1, "meter"),                  # Distance / displacement
        "x": Q_(1, "meter"),                  # Position
        "t": Q_(1, "second"),                 # Time
        "p": Q_(1, "kilogram*meter/second"),  # Momentum

        # Energy & Work
        "E": Q_(1, "joule"),                  # Energy
        "W": Q_(1, "joule"),                  # Work
        "KE": Q_(1, "joule"),                 # Kinetic energy
        "PE": Q_(1, "joule"),                 # Potential energy
        "P": Q_(1, "watt"),                   # Power

        # Electricity & Magnetism
        "q": Q_(1, "coulomb"),                # Charge
        "V": Q_(1, "volt"),                   # Voltage
        "I": Q_(1, "ampere"),                 # Current
        "R": Q_(1, "ohm"),                    # Resistance
        "C": Q_(1, "farad"),                  # Capacitance
        "L": Q_(1, "henry"),                  # Inductance
        "B": Q_(1, "tesla"),                  # Magnetic field
        "phi": Q_(1, "weber"),                # Magnetic flux

        # Thermodynamics
        "T": Q_(1, "kelvin"),                 # Temperature
        "k": Q_(1, "joule/kelvin"),           # Boltzmann constant (J/K)
        "R_gas": Q_(1, "joule/(mol*kelvin)"), # Gas constant
        "n": Q_(1, "mole"),                   # Amount of substance
        "p_pressure": Q_(1, "pascal"),        # Pressure
        "V_volume": Q_(1, "meter**3"),        # Volume
        "Q_heat": Q_(1, "joule"),             # Heat

        # Waves & Optics
        "f": Q_(1, "hertz"),                  # Frequency
        "lambda_": Q_(1, "meter"),            # Wavelength
        "c": Q_(299792458, "meter/second"),   # Speed of light
        "omega": Q_(1, "radian/second"),      # Angular frequency

        # Constants
        "G": Q_(6.674e-11, "meter**3 / (kilogram * second**2)"),  # Gravitational constant
        "h": Q_(6.626e-34, "joule*second"),   # Planck constant
        "e": Q_(1.602e-19, "coulomb"),        # Elementary charge
        }
        
        # Add custom variables if provided
        if session_config.custom_variables:
            try:
                custom_vars = {}
                for var_def in session_config.custom_variables.split(','):
                    if '=' in var_def:
                        var_name, unit_expr = var_def.strip().split('=', 1)
                        var_name = var_name.strip()
                        unit_expr = unit_expr.strip()
                        # Evaluate the unit expression - handle both pure units and quantities with values
                        try:
                            # First try as a pure unit expression
                            custom_vars[var_name] = Q_(1, unit_expr)
                        except Exception:
                            # If that fails, try evaluating the expression directly
                            # This handles cases like "9.81*meter/second**2"
                            custom_vars[var_name] = eval(unit_expr, {}, {"Q_": Q_, "ureg": ureg})
                base_context.update(custom_vars)
            except Exception as e:
                # If parsing fails, continue with base context
                print(f"Warning: Failed to parse custom variables: {e}")
        
        return base_context

    def check_equation_sanity(equation: str, context: Dict[str, Any], verbose: bool = False) -> dict:
        """
        Check if an equation is dimensionally consistent, with context.
        Returns a dict with:
          - consistent: True/False
          - lhs_units: unit string
          - rhs_units: unit string
          - message: human-readable explanation
        """
        try:
            lhs, rhs = equation.split("=")
            lhs_expr, rhs_expr = lhs.strip(), rhs.strip()

            lhs_val = eval(lhs_expr, {}, context)
            rhs_val = eval(rhs_expr, {}, context)

            lhs_units = str(lhs_val.units)
            rhs_units = str(rhs_val.units)

            if lhs_val.check(rhs_val):
                result = {
                    "equation": equation,
                    "consistent": True,
                    "lhs_units": lhs_units,
                    "rhs_units": rhs_units,
                    "message": f"✅ Equation is dimensionally consistent: both sides are [{lhs_units}]."
                }
            else:
                result = {
                    "equation": equation,
                    "consistent": False,
                    "lhs_units": lhs_units,
                    "rhs_units": rhs_units,
                    "message": f"❌ Equation is NOT consistent: LHS is [{lhs_units}] but RHS is [{rhs_units}]."
                }
            
            if verbose:
                result["verbose"] = {
                    "lhs_expression": lhs_expr,
                    "rhs_expression": rhs_expr,
                    "lhs_magnitude": float(lhs_val.magnitude),
                    "rhs_magnitude": float(rhs_val.magnitude)
                }
            
            return result
        except Exception as e:
            return {
                "equation": equation,
                "consistent": False,
                "lhs_units": None,
                "rhs_units": None,
                "message": f"❌ Error while checking equation: {e}"
            }

    # Add equation sanity checker tool
    @server.tool()
    def check_equation(equation: str, ctx: Context) -> str:
        """Check if a physics equation is dimensionally consistent.
        
        Examples:
        - "F = m * a" (Newton's second law)
        - "E = m * c**2" (Einstein's mass-energy equivalence)
        - "V = I * R" (Ohm's law)
        - "d = v * t" (distance = velocity * time)
        - "g = 9.81 * meter/second**2" (custom gravitational acceleration)
        """
        session_config = ctx.session_config
        context = build_context(session_config)
        result = check_equation_sanity(equation, context, session_config.verbose_output)
        
        if session_config.verbose_output and "verbose" in result:
            verbose_info = result["verbose"]
            return f"{result['message']}\n\nDetailed Analysis:\n- LHS: {verbose_info['lhs_expression']} = {verbose_info['lhs_magnitude']} [{result['lhs_units']}]\n- RHS: {verbose_info['rhs_expression']} = {verbose_info['rhs_magnitude']} [{result['rhs_units']}]"
        else:
            return result["message"]

    # Add custom variables management tool
    @server.tool()
    def add_custom_variable(name: str, unit: str, ctx: Context) -> str:
        """Add a custom variable to the context for equation checking.
        
        Args:
            name: Variable name (e.g., 'g', 'A', 'rho')
            unit: Unit expression (e.g., '9.81*meter/second**2', 'meter**2', 'kilogram/meter**3')
        
        Examples:
            add_custom_variable("g", "9.81*meter/second**2")  # Gravitational acceleration
            add_custom_variable("A", "meter**2")              # Area
            add_custom_variable("rho", "kilogram/meter**3")   # Density
        """
        session_config = ctx.session_config
        
        # Parse current custom variables
        current_vars = {}
        if session_config.custom_variables:
            try:
                for var_def in session_config.custom_variables.split(','):
                    if '=' in var_def:
                        var_name, unit_expr = var_def.strip().split('=', 1)
                        current_vars[var_name.strip()] = unit_expr.strip()
            except Exception:
                pass
        
        # Add new variable
        current_vars[name] = unit
        
        # Rebuild the custom_variables string
        new_custom_vars = ','.join([f"{k}={v}" for k, v in current_vars.items()])
        
        # Update the session config (this is a read-only context, so we'll return instructions)
        return f"✅ Custom variable '{name}' with unit '{unit}' added.\n\n" \
               f"To use this variable, restart the server with:\n" \
               f"custom_variables='{new_custom_vars}'\n\n" \
               f"Example usage in equations:\n" \
               f"- 'h = 0.5 * g * t**2' (height with gravitational acceleration)\n" \
               f"- 'F = rho * A * v**2' (force with density and area)"

    # Add units listing tool
    @server.tool()
    def list_units(ctx: Context) -> str:
        """List all available physical units and constants for equation checking.
        
        Returns a categorized list of symbols with their units and descriptions.
        """
        session_config = ctx.session_config
        context = build_context(session_config)
        
        # Categorize units
        categories = {
            "Mechanics": {
                "F": "Force (newton)",
                "m": "Mass (kilogram)", 
                "a": "Acceleration (meter/second²)",
                "v": "Velocity (meter/second)",
                "u": "Initial velocity (meter/second)",
                "d": "Distance/displacement (meter)",
                "x": "Position (meter)",
                "t": "Time (second)",
                "p": "Momentum (kilogram·meter/second)"
            },
            "Energy & Work": {
                "E": "Energy (joule)",
                "W": "Work (joule)",
                "KE": "Kinetic energy (joule)",
                "PE": "Potential energy (joule)",
                "P": "Power (watt)"
            },
            "Electricity & Magnetism": {
                "q": "Charge (coulomb)",
                "V": "Voltage (volt)",
                "I": "Current (ampere)",
                "R": "Resistance (ohm)",
                "C": "Capacitance (farad)",
                "L": "Inductance (henry)",
                "B": "Magnetic field (tesla)",
                "phi": "Magnetic flux (weber)"
            },
            "Thermodynamics": {
                "T": "Temperature (kelvin)",
                "k": "Boltzmann constant (joule/kelvin)",
                "R_gas": "Gas constant (joule/(mol·kelvin))",
                "n": "Amount of substance (mole)",
                "p_pressure": "Pressure (pascal)",
                "V_volume": "Volume (meter³)",
                "Q_heat": "Heat (joule)"
            },
            "Waves & Optics": {
                "f": "Frequency (hertz)",
                "lambda_": "Wavelength (meter)",
                "c": "Speed of light (299792458 m/s)",
                "omega": "Angular frequency (radian/second)"
            }
        }
        
        constants = {
            "G": "Gravitational constant (6.674×10⁻¹¹ m³/(kg·s²))",
            "h": "Planck constant (6.626×10⁻³⁴ J·s)",
            "e": "Elementary charge (1.602×10⁻¹⁹ C)"
        }
        
        output = "🔬 Available Physical Units and Constants\n\n"
        
        for category, units in categories.items():
            output += f"## {category}\n"
            for symbol, description in units.items():
                output += f"- **{symbol}**: {description}\n"
            output += "\n"
        
        if session_config.include_constants:
            output += "## Physical Constants\n"
            for symbol, description in constants.items():
                output += f"- **{symbol}**: {description}\n"
            output += "\n"
        
        # Add custom variables if any
        if session_config.custom_variables:
            output += "## Custom Variables\n"
            try:
                for var_def in session_config.custom_variables.split(','):
                    if '=' in var_def:
                        var_name, unit_expr = var_def.strip().split('=', 1)
                        var_name = var_name.strip()
                        unit_expr = unit_expr.strip()
                        if var_name in context:
                            unit_str = str(context[var_name].units)
                            output += f"- **{var_name}**: {unit_str}\n"
            except Exception as e:
                output += f"- Error: {e}\n"
            output += "\n"
        
        output += "💡 **Usage**: Use these symbols in equations like 'F = m * a' or 'E = m * c**2'\n"
        output += "🔍 **Note**: Use 'lambda_' for wavelength (lambda is a Python keyword)\n"
        output += "⚙️ **Custom Variables**: Use the 'add_custom_variable' tool to add your own variables"
        
        return output

    # Add a resource
    @server.resource("physics://dimensional-analysis")
    def dimensional_analysis_guide() -> str:
        """Guide to dimensional analysis and equation validation."""
        return (
            "Dimensional analysis is a powerful tool in physics for checking "
            "the consistency of equations. Every physical quantity has dimensions "
            "expressed in terms of fundamental units: length [L], mass [M], time [T], "
            "electric current [I], thermodynamic temperature [Θ], amount of substance [N], "
            "and luminous intensity [J].\n\n"
            "Key principles:\n"
            "1. Both sides of an equation must have the same dimensions\n"
            "2. Arguments to transcendental functions (sin, cos, exp, log) must be dimensionless\n"
            "3. Dimensional analysis can reveal errors in equations before numerical calculations\n"
            "4. It helps derive relationships between physical quantities\n\n"
            "Available tools:\n"
            "- check_equation: Validate dimensional consistency\n"
            "- list_units: Show all available units and variables\n"
            "- add_custom_variable: Add your own variables to the context\n\n"
            "Custom variables can be added via configuration or the add_custom_variable tool. "
            "Example: custom_variables='g=9.81*meter/second**2,A=meter**2'"
        )

    # Add a prompt
    @server.prompt()
    def analyze_equation(equation: str) -> list:
        """Generate a prompt for analyzing a physics equation."""
        return [
            {
                "role": "user",
                "content": f"Please analyze this physics equation for dimensional consistency: {equation}. "
                          f"Use the check_equation tool to verify it, and explain what the equation represents "
                          f"and whether it's physically meaningful.",
            },
        ]

    return server
