# Integration Tests

Integration tests require actual API keys. To run these tests:

1. Install dotenvx:
   ```bash
   curl -fsSL https://dotenvx.sh | sh
   ```

2. Create an encrypted .env.test file:
   ```bash
   # Add your API key
   echo "OPENROUTER_API_KEY=your-actual-api-key" > .env.test

   # Encrypt the file
   dotenvx encrypt .env.test
   ```

3. Run integration tests:
   ```bash
   dotenvx run -f .env.test -- pytest -m integration
   ```

Note: The .env.test file should be added to .gitignore and not committed to the repository.
