#!/usr/bin/env python3
"""
Start script for AWS Amplify and other cloud platforms
"""

import os
import sys
from main import app

# Get port from environment variable or default to 8080
port = int(os.environ.get("PORT", 8080))

if __name__ == "__main__":
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)