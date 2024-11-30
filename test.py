import jinja2

# Load the template
template = jinja2.Template("Hello, {{ 名称 }}!")

# Render the template with the provided data
output = template.render(名称="World")

# Print the output
print(output)