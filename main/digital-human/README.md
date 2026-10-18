This is a development document. To deploy the XiaoZhi server, [click here for the deployment tutorial](../../README.md#deployment-documentation)

For all-in-one digital human deployment, Kiosk full-screen startup, and system environment configuration, [see the all-in-one deployment guide](../../docs/all-in-one-digital-human-setup.md)

For wake word model downloads, runtime configuration, and detailed usage instructions, [see the dedicated wake word documentation](../../docs/digital-human-wakeword.md)

# Project Introduction

digital-human is a standalone digital human testing module that provides a local test page, frontend interaction assets, a wake word runtime, and event bridge capabilities for integration testing of the entire digital human interaction chain.

# Quick Start

Install dependencies:

```bash
pip install -r wakeword_runtime/requirements.txt
```

Start the module:

```bash
python start.py
```

# Access URLs

After startup, the following are available:

- Page URL: http://127.0.0.1:8006/index.html
- Event bridge URL: ws://127.0.0.1:8006/wakeword-ws
- Health check: http://127.0.0.1:8006/health

# Directory Overview

- `start.py`: module entry point
- `index.html`: digital human test page entry
- `wakeword_runtime`: local wake word runtime and configuration directory
- `js`, `css`: frontend page scripts and styles
- `images`, `resources`: page asset files

# Related Documentation

- All-in-one deployment guide: for full-machine deployment on x86 devices, Kiosk display, and boot autostart configuration
	[../../docs/all-in-one-digital-human-setup.md](../../docs/all-in-one-digital-human-setup.md)
- Dedicated wake word documentation: for wake word model downloads, runtime configuration, and local debugging instructions
	[../../docs/digital-human-wakeword.md](../../docs/digital-human-wakeword.md)
