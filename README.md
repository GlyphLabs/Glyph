Glyph's code is open source for safety purposes only. You can still use our code, but you are not allowed to claim that it's yours, we will have to reach out to you.

# cotntributing
## getting started
this project uses the [rye](https://rye.astral.sh/) package manager to manage dependencies. you can find the commands to install rye from the website.

to install the dependencies, run `rye sync`.

### environment variables
some configuration values are stored using environment variables. by default, the code is able to load `.env` files. 
you can find the required variables in the `.env.example` file.

### running the bot
to run the bot, you can run the `main.py` file. you should first enter the python environment by running `. .venv/bin/activate` on linux or `.venv\Scripts\activate` on windows.
## about the code
Glyph's code is divided into 3 main parts:

### the core (`src/bot`)
this is where the primary code is located. the core could essentially run on it's own.

### the cogs (`src/cogs`)
this is where the commands are located. the cogs are loaded into the core and are used to extend the functionality of the bot. almost all commands are located in the cogs.

### the db code (`src/db.py`)
this is where the database code is located. the db code is used to interact with the database and store data.