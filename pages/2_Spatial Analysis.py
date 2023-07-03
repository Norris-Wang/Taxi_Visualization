import pandas as pd 
import numpy as np
import streamlit as st
from sklearn.cluster import MiniBatchKMeans
import folium
from streamlit_folium import folium_static
import branca.colormap as cm

st.set_page_config(page_title="Spatial Analysis",
                   page_icon="🗺️",
                   layout='wide')

st.title('Spatial Analysis 🗺️')
st.caption('In this page, you can analyze the data from a aspect of space.')

def Check_Data_Exitence():
    try:
        data = st.session_state.data
        return data
    except (AttributeError, NameError):
        st.error('No data to be analyzed! Please turn to the *Home* page and upload a file.')
        st.stop()

def Get_Address(lat, lon):
    import requests
    from bs4 import BeautifulSoup

    url = 'http://api.map.baidu.com/reverse_geocoding/v3/?location='
    output = 'json'
    ak = 'tMG72CSgxsa9dBOYyLOoUvKvDb7iBHwH'

    uri = url+'&output=' + output + '&ak=' + ak + '&location=' + str(lat) + ',' + str(lon)
    html = requests.get(uri)
    info = BeautifulSoup(html.text,'lxml')
    address = eval(info.p.text)["result"]["formatted_address"]
    return address

# 继承主页面中输入文件的数据
data = Check_Data_Exitence()
ID_list = st.session_state['ID_list']
Min_Duration = st.session_state.Min_Duration
Max_Duration = st.session_state.Max_Duration

st.divider()
  
GetOn = data.loc[:,['ID', 'GetOnTime', 'GetOnLon', 'GetOnLat','Duration']]
GetOn.columns = ['ID', 'time', 'lon', 'lat','Duration']


# 热点分析
st.header("Hot Spot Analysis on Get-On Data")
st.caption("Here you can divide the **get-on** points into several different areas, \
           and get the center of the area (hereinafter called a _hot spot_.)")

# 计算热点经纬度
num_clusters = st.slider(label='Select the number of areas you want to divide the points into.',
                         min_value=1, max_value=20, value=3)
batch_size = 4096  # Mini Batch大小
kmeans = MiniBatchKMeans(n_clusters=num_clusters, batch_size=batch_size, n_init='auto')
kmeans.fit(data[['GetOnLat', 'GetOnLon']])
GetOn["ClusterID"] = kmeans.labels_
hotspots = pd.DataFrame(kmeans.cluster_centers_, columns=['Lat', 'Lon'])

# 获取热点地理编码
address_list = []
for i in range(len(hotspots)):
    lat, lon = hotspots.iloc[i,0], hotspots.iloc[i,1]
    address = Get_Address(lat, lon)
    address_list.append(address)
hotspots["Address"] = address_list

map_hotspot = folium.Map(location=[data['GetOnLat'].mean(), data['GetOnLon'].mean()], zoom_start=10, tiles='cartodbpositron')

# 显示各区域点
GetOn_displayed = GetOn.sample(frac=.001)
colormap_cluster = cm.LinearColormap(colors=['yellow', 'pink', 'orange', 'blue'],
                            vmin=GetOn.ClusterID.min(), vmax=GetOn.ClusterID.max())
for i in range(len(GetOn_displayed)):
    point = GetOn_displayed.iloc[i,:]
    lat, lon, cluster = point.lat, point.lon, point.ClusterID
    folium.CircleMarker(location=[lat, lon],
                        radius=4, color=colormap_cluster(cluster), fill=False).add_to(map_hotspot)

# 显示热点位置
for i in range(len(hotspots)):
    hotspot = hotspots.iloc[i,:]
    lat, lon, address = hotspot[0], hotspot[1], hotspot[2]
    tooltip_hotspot = folium.Tooltip(f"""
                             <b>Latitude</b>: {round(lat,2)} N, <b>Longitude</b>: {round(lon,2)} E <br />
                             <b>Address</b>: {address}""")
    folium.CircleMarker(location=[lat, lon],
                        radius=10, color='red', fill=True, fill_color='red',
                        tooltip=tooltip_hotspot).add_to(map_hotspot)

plot_hotspot = folium_static(map_hotspot)

st.divider()

# 显示出租车运行起止点
st.header('Taxi Route')
st.caption("Here you can select several taxis and get its track.")

ID_selected = st.multiselect(label="Select a taxi ID", 
             options=sorted(list(set(data.ID))),
             default=list(set(data.ID))[:3])
if ID_selected == []:
    st.stop()
data_selected = data.query("ID in @ID_selected")

st.write("You select", len(ID_selected), "taxi(s), including", len(data_selected), "record(s).\
         Here are the records:")
st.dataframe(data_selected, hide_index=True)

map_route = folium.Map(location=[data_selected['GetOnLat'].mean(), data_selected['GetOnLon'].mean()],
                 zoom_start=10, tiles='cartodbpositron')
colormap_route = cm.LinearColormap(colors=['red', 'blue', 'yellow', 'pink', 'green'],
                                   vmin=np.array(ID_selected).min(), vmax=np.array(ID_selected).max())

for i in range(len(data_selected)):
    record = data_selected.iloc[i, :]
    ID =  record.ID
    start = [record.GetOnLat, record.GetOnLon]
    end = [record.GetOffLat, record.GetOffLon]
    duration = record.Duration//60
    tooltip_route = folium.Tooltip(f"""
                                   <b>Taxi ID</b>: {ID}<br/>
                                   <b>Duration</b>: {duration}<br/>
                                   <b>Start</b>: {Get_Address(start[0], start[1])}</br>
                                   <b>End</b>: {Get_Address(end[0], end[1])}
                                   """)
    folium.PolyLine(locations=(start, end),
                    color=colormap_route(ID),
                    tooltip=tooltip_route,alpha=.5).add_to(map_route)
plot_route = folium_static(map_route)
