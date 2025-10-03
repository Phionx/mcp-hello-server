#!/bin/bash

# Navigate to the MCP project directory
cd /Users/phionx/Github/r2/mcp

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: MCP Hello Server"

# Create GitHub repository (you'll need to run this manually or provide your GitHub username)
echo "To create the GitHub repository, run:"
echo "gh repo create mcp-hello-server --public --description 'MCP Hello Server - A simple Model Context Protocol server built with Smithery' --source=. --remote=origin --push"

echo "Or if you prefer to do it manually:"
echo "1. Go to https://github.com/new"
echo "2. Create a new repository named 'mcp-hello-server'"
echo "3. Then run: git remote add origin https://github.com/YOUR_USERNAME/mcp-hello-server.git"
echo "4. Then run: git push -u origin main"
