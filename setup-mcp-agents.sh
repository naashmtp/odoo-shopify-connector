#!/bin/bash

# Setup script for the best MCP servers and Claude Code subagents
# Author: Generated for optimal development environment

echo "🚀 Setting up Claude Code MCP Servers and Subagents..."

# Create necessary directories
mkdir -p ~/.claude/agents
mkdir -p ~/.claude/config

# Install Node.js packages for MCP servers
echo "📦 Installing MCP servers..."

# Essential MCP servers
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-filesystem
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @modelcontextprotocol/server-postgres
npm install -g @modelcontextprotocol/server-sqlite
npm install -g @microsoft/playwright-mcp
npm install -g @punkpeye/mcp-server-puppeteer
npm install -g @punkpeye/mcp-server-docker
npm install -g @azure/mcp-server-azure-devops

# Python packages for code execution
pip install pydantic-ai-mcp-server

echo "🤖 Installing Claude Code Subagents Collections..."

# Install the best subagent collections
cd ~/.claude/agents

# 100+ mega-collection (0xfurai)
echo "Installing mega-pack (100+ agents)..."
git clone https://github.com/0xfurai/claude-code-subagents.git mega-pack

# Production-ready collection (wshobson)
echo "Installing production pack (48 agents)..."
git clone https://github.com/wshobson/agents.git production-pack

# Specialized collection (lst97)
echo "Installing specialized pack (33 agents)..."
git clone https://github.com/lst97/claude-code-sub-agents.git specialized-pack

# Comprehensive collection
echo "Installing comprehensive pack..."
git clone https://github.com/VoltAgent/awesome-claude-code-subagents.git awesome-pack

# Rahul's collection
echo "Installing awesome agents..."
git clone https://github.com/rahulvrane/awesome-claude-agents.git rahul-pack

echo "⚙️ Setting up global MCP configuration..."

# Create global Claude MCP configuration
cat > ~/.claude/config.json << 'EOF'
{
  "mcp": {
    "servers": {
      "github": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
        }
      },
      "filesystem": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-filesystem", "${HOME}"]
      },
      "brave-search": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "${BRAVE_API_KEY}"
        }
      },
      "postgres": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-postgres"],
        "env": {
          "POSTGRES_CONNECTION_STRING": "${POSTGRES_URL}"
        }
      },
      "playwright": {
        "command": "npx",
        "args": ["@microsoft/playwright-mcp"]
      },
      "sqlite": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-sqlite", "--db-path", "./data.db"]
      },
      "docker": {
        "command": "npx",
        "args": ["@punkpeye/mcp-server-docker"]
      },
      "python-exec": {
        "command": "python",
        "args": ["-m", "pydantic_ai_mcp_server"]
      },
      "azure-devops": {
        "command": "npx",
        "args": ["@azure/mcp-server-azure-devops"],
        "env": {
          "AZURE_DEVOPS_TOKEN": "${AZURE_DEVOPS_TOKEN}",
          "AZURE_DEVOPS_ORG": "${AZURE_DEVOPS_ORG}"
        }
      }
    }
  }
}
EOF

echo "🔑 Setting up environment variables template..."

# Create environment template
cat > ~/.claude/.env.template << 'EOF'
# GitHub Personal Access Token
# Get from: https://github.com/settings/tokens
GITHUB_TOKEN=your_github_token_here

# Brave Search API Key
# Get from: https://api.search.brave.com/app/keys
BRAVE_API_KEY=your_brave_api_key_here

# PostgreSQL connection (optional)
POSTGRES_URL=postgresql://user:password@localhost:5432/database

# Azure DevOps (optional)
AZURE_DEVOPS_TOKEN=your_azure_devops_token
AZURE_DEVOPS_ORG=your_organization_name
EOF

echo "📋 Creating agent management script..."

# Create agent management script
cat > ~/.claude/manage-agents.sh << 'EOF'
#!/bin/bash

case "$1" in
  "list")
    echo "Available agent collections:"
    ls -la ~/.claude/agents/
    ;;
  "update")
    echo "Updating all agent collections..."
    cd ~/.claude/agents
    for dir in */; do
      if [ -d "$dir/.git" ]; then
        echo "Updating $dir..."
        cd "$dir"
        git pull
        cd ..
      fi
    done
    ;;
  "backup")
    echo "Creating backup of agents..."
    tar -czf ~/.claude/agents-backup-$(date +%Y%m%d).tar.gz ~/.claude/agents/
    echo "Backup created: ~/.claude/agents-backup-$(date +%Y%m%d).tar.gz"
    ;;
  *)
    echo "Usage: $0 {list|update|backup}"
    echo "  list   - List all agent collections"
    echo "  update - Update all git-based collections"
    echo "  backup - Create backup of all agents"
    ;;
esac
EOF

chmod +x ~/.claude/manage-agents.sh

echo "🎯 Creating project-specific MCP config..."

# Update the project's .mcp.json with enhanced configuration
cat > .mcp.json << 'EOF'
{
  "servers": {
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-filesystem",
        "."
      ]
    },
    "python-exec": {
      "command": "python",
      "args": ["-m", "pydantic_ai_mcp_server"]
    },
    "sqlite": {
      "command": "npx",
      "args": [
        "@modelcontextprotocol/server-sqlite",
        "--db-path",
        "./odoo_shopify.db"
      ]
    },
    "docker": {
      "command": "npx",
      "args": ["@punkpeye/mcp-server-docker"]
    }
  }
}
EOF

echo "✅ Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Copy ~/.claude/.env.template to ~/.claude/.env and fill in your API keys"
echo "2. Restart Claude Code to load the new MCP servers"
echo "3. Use 'claude agents' to see available subagents"
echo "4. Use '~/.claude/manage-agents.sh list' to manage agent collections"
echo ""
echo "🎉 You now have access to:"
echo "   • 200+ specialized subagents across 5 collections"
echo "   • 10 powerful MCP servers for development"
echo "   • Optimized configuration for Odoo/Shopify development"
echo ""
echo "Happy coding! 🚀"