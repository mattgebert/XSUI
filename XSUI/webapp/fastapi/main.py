from fastapi import FastAPI
import tempfile, os
import sqlite3
import sqlalchemy as sa
import sqlalchemy.orm as orm
import uvicorn
from XSUI.webapp.fastapi.dash_tabs.dash_main import dash_app
from fastapi.middleware.wsgi import WSGIMiddleware


temp_dir = tempfile.gettempdir()
temp_sqlite_db = os.path.join(temp_dir, "XSUI_sqlite.db")

# Initialize the app
app = FastAPI()

# Mount the Dash app to the FastAPI app
app.mount("/dashboard1/", WSGIMiddleware(dash_app.server))

# Initialize the database connection
db = sa.create_engine(f"sqlite:///{temp_sqlite_db}", echo=True)


from XSUI.webapp.fastapi.models import bases_list_all

# Create all tables in the database
created_tables = []
for base in bases_list_all:
    base.metadata.create_all(db)

    # Collect the names of created tables
    created_tables += base.metadata.tables.keys()
print(f"Created tables: {created_tables}")

session_status: dict = {
    "calibrant": None,
    # "poni" :
}


@app.get("/")
async def root():
    """The root home endpoint for the XSUI web application."""
    return {"message": "Hello World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    """Get an item by its ID."""
    return {"item_id": item_id}


if __name__ == "__main__":
    # with orm.Session(db) as session:
    import webbrowser

    webbrowser.open("http://localhost:8000/dashboard1/", new=2)
    uvicorn.run(app, host="0.0.0.0", port=8000)

# https://gist.github.com/rajesh-ae/70666702104aacb2d42e95504fcefba9
# from fastapi import FastAPI, Response
# import plotly.express as px
# from pydantic import BaseModel, JsonValue
# import json
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins="*",
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# class PlotlyJSONSchema(BaseModel):
#     data: JsonValue
#     layout: JsonValue

# @app.get("/plotly_data", response_model=PlotlyJSONSchema)
# async def plotly_data():
#     df = px.data.gapminder().query("continent == 'Oceania'")
#     fig = px.line(df, x='year', y='lifeExp', color='country', markers=True)
#     this_plot_data = fig.to_json(pretty=True, engine="json")
#     this_plot_data = json.loads(this_plot_data)
#     return PlotlyJSONSchema(data=this_plot_data["data"], layout=this_plot_data["layout"])
#     # return Response(content=this_plot_data, media_type="application/json")
