import os


def find_requirements_files(root_dir):
    """Recursively search for requirement*.txt files in the directory structure."""
    requirements_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith("requirements") and filename.endswith(".txt"):
                requirements_files.append(os.path.join(dirpath, filename))
    return requirements_files


def read_dependencies_from_file(file_path):
    """Read the dependencies from a requirements file."""
    with open(file_path, 'r') as file:
        return file.readlines()


def format_dependency(line):
    """Format a dependency line for pyproject.toml."""
    operators = ['==', '>=', '<=', '>', '<']
    for op in operators:
        if op in line:
            package, version = line.split(op)
            return f'{package.strip()} = "{op}{version.strip()}"'
    # Default to wildcard version if not specified
    return f'{line.strip()} = "*"'


def generate_toml(root_dir):
    """Generate pyproject.toml content based on the found requirements*.txt files."""
    requirements_files = find_requirements_files(root_dir)
    toml_content = '[tool.poetry.dependencies]\npython = "^3.11"\n\n'

    for req_file in requirements_files:
        # Generating the section header
        section_elements = req_file.replace(
            root_dir, "").split(os.path.sep)[1:-1]
        section_name = ".".join(section_elements).replace("requirements.", "")

        # If there's no section name, it means it's a common dependency
        if not section_name:
            section_name = "common"

        toml_content += f"[{section_name}]\n"

        # Adding the dependencies for this section
        deps = read_dependencies_from_file(req_file)
        for dep in deps:
            if dep.strip() and not dep.startswith('#'):  # Exclude empty lines and comments
                toml_content += format_dependency(dep) + '\n'
        toml_content += '\n'

    return toml_content


def main():
    root_dir = '.'  # Run from current directory
    toml_content = generate_toml(root_dir)
    with open("pyproject.toml", "w") as toml_file:
        toml_file.write(toml_content)
    print("pyproject.toml generated!")


if __name__ == "__main__":
    main()
