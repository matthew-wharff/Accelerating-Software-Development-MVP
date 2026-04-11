from dotenv import load_dotenv
load_dotenv()
from e2b_code_interpreter import Sandbox  # noqa: E402

sandbox = Sandbox.create()  # Needs E2B_API_KEY environment variable
result = sandbox.commands.run('echo "Hello from E2B Sandbox!"')
print(result.stdout)
