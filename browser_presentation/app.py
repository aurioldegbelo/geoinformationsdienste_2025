import os
import streamlit as st
from streamlit_folium import st_folium
import time

# import functions from stac_pipepine.py
from stac_pipeline import (
    make_llm,
    get_stac_collections,
    extract_search_params,
    geocode_first_bbox,
    folium_bbox_map,
    search_stac,
    summarize_results,
)

st.set_page_config(page_title="STAC Geosearch Chat", page_icon="🗺️", layout="wide")
st.title("STAC Geosearch Chat")

with st.sidebar:
    st.subheader("LLM Settings")
    
    api_base = st.text_input("API Base", value=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))
    api_key = st.text_input("API Key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
   # model_name = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "llama-3.3-70b-instruct"))
    model_name = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1) # controls deterministic vs. random

    st.caption("Tip: set these in your environment so you don't need to paste them every time.")

os.environ["OPENAI_API_BASE"] = api_base
os.environ["OPENAI_API_KEY"] = api_key


if "current_state" not in st.session_state:
    st.session_state.current_state = "get_user_query"
    st.session_state.last_bbox = None
    st.session_state.last_bbox_name = None
    st.session_state.last_params = None
    st.session_state.last_query = None


# Build LLM
llm = make_llm(model=model_name, temperature=temperature)

# Chat input
query = st.chat_input("Ask for data (e.g., 'Find LST data for the summer 2018 for the two largest cities in Germany.')")


if query:
   
    with st.chat_message("user"):
        st.markdown(query)

    with st.spinner(" Extracting parameters with LLM…"):
        t1 = time.time()
        collections = get_stac_collections()
        print("Parameter extraction started...")

        params = extract_search_params(query, collections, llm)
        t2 = time.time()

        print("Parameters extracted: ", params)
        print(f'Parameter extraction took {t2-t1} seconds')

        # update the session states with the new values
        with st.spinner(" Geocoding location…"):
            print("Location geocoding started: ", params)
            bbox, bbox_name = geocode_first_bbox(params["location"])
            t3 = time.time()
            print ("Bounding box extracted is: ", bbox)
            st.session_state.last_bbox = bbox
            st.session_state.last_bbox_name = bbox_name
            st.session_state.last_params = params
            st.session_state.current_state = "results_available" # state that the results are available

# say what to do if the results become available
if (st.session_state.current_state == "results_available"):

    # retrieve the latest values from the session states variable
    extracted_params = st.session_state.last_params
    extracted_bbox =  st.session_state.last_bbox
    extracted_bbox_name =  st.session_state.last_bbox_name

    # display the parameters extracted
    with st.expander("Debug: extracted parameters", expanded=True):
            st.json(extracted_params)

    # alternative way of showing the parameters extracted
    st.write({"bbox": extracted_bbox, "bbox_name": extracted_bbox_name})
    st.subheader("Area of Interest")
    # map create the map with the bbox and the bbox names extracted
    fmap = folium_bbox_map(extracted_bbox, extracted_bbox_name)
    st_folium(fmap, width=900, height=500)   




