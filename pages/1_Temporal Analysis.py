import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

st.set_page_config(page_title="Temporal Analysis", page_icon="⏱️",
                   layout='wide', initial_sidebar_state='collapsed')
# 设置主体宽度
st.markdown(
    f"""
    <style>
    .main .block-container {{
        max-width: 1400px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

def Check_Data_Exitence():
    try:
        data = st.session_state.data
        return data
    except (AttributeError, NameError):
        st.error('No data to be analyzed! Please turn to the *Home* page and upload a file.')
        st.stop()

st.title('Temporal Analysis ⏱️')
st.caption('In this page, you can analyze the data from a aspect of time.')

# 继承主页面中输入文件的数据
data = Check_Data_Exitence()
data['HH'] = data.GetOnTime.str.slice(-8,-6).astype(int)
data['MM'] = data.GetOnTime.str.slice(-5,-3).astype(int)
data['SS'] = data.GetOnTime.str.slice(-2).astype(int)
data['Duration(min)'] = data.Duration//60
st.session_state['data'] = data

st.divider()

column1, column2 = st.columns(2, gap='large')

with column1:
    # 乘车时长的频率分布
    st.subheader('Basic Statistic of Duration')
    st.caption('Here we calculate the frequency of diffent durations。')
    Raw_Time_data = data[['Duration','HH','MM','SS']]
    Raw_Time_data['Duration(min)'] = Raw_Time_data.Duration//60
    Min_Duration = st.session_state.Min_Duration
    Max_Duration = st.session_state.Max_Duration

    # 异常值筛选
    if st.checkbox(label='Remove the anormaly based on the duration',):
        anormaly_min, anormaly_max = st.select_slider(
            label='Select the bound beyond which you regard the anormaly is',
            options=sorted(list(set(Raw_Time_data['Duration(min)'].values))),
            value=(Min_Duration, Max_Duration))
        Time_data = Raw_Time_data[(Raw_Time_data['Duration(min)']>=anormaly_min) &
                                (Raw_Time_data['Duration(min)']<=anormaly_max)]
    else:
        Time_data = Raw_Time_data

    duration_frequncy = pd.DataFrame(Time_data['Duration(min)'].value_counts().sort_index().reset_index())
    duration_frequncy.columns = ['duration', 'frequency']
    duration_frequncy_plot = px.bar(data_frame=duration_frequncy,
                                    x='duration', y='frequency',
                                    labels={'x':'Duration(min)', 'y':'Frequency'})
    st.plotly_chart(duration_frequncy_plot)
    duration_description = pd.DataFrame(Time_data['Duration(min)'].describe())
    st.dataframe(duration_description.T, use_container_width=True)

with column2:
    # 以小时为单位进行统计
    st.subheader('Statistic in Each Hour')
    st.write("The figure below shows the relation among get-on time, number of orders, and duration.")
    Hour_Statistic = Time_data.groupby('HH').agg({'Duration(min)':'mean','HH':'count'})
    Hour_Statistic.columns = ['Average_Duration(min)', 'Count']
    Hour_Statistic = Hour_Statistic.reset_index()
    Hour_Statistic.columns = ['Hour', 'Average Duration(min)', 'Count']
    Hour_Statistic_Plot = alt.Chart(Hour_Statistic).mark_bar().encode(alt.X('Hour'),alt.Y('Count'),alt.Color('Average Duration(min)')).interactive()
    st.caption("X -- 24 hours in one day. Label _0_ stands for _00:00:00_ to _00:59:00_, and so on.")
    st.caption("Y -- the number of orders in each hour")
    st.caption("color of bars -- the average duration in each hour")
    st.altair_chart(Hour_Statistic_Plot, use_container_width=True)
    st.caption("_Notice that the figure on the right synchronize with the change of anormaly range. \
               In addition, the color scale bar doesn't keep fixed. That's to say, \
               the same average duration may be given different colors before and after \
               you change the anormaly range by sliding the slider._")
    

# 分别存放上车和下车数据
GetOn = data.loc[:,['ID', 'GetOnTime', 'GetOnLon', 'GetOnLat','Duration']]
GetOn.columns = ['ID', 'GetOnTime', 'lon', 'lat','Duration']
GetOff = data.loc[:,['ID', 'GetOffTime', 'GetOffLon', 'GetOffLat','Duration']]
GetOff.columns = ['ID', 'GetOffTime', 'lon', 'lat','Duration']

st.divider()

if st.checkbox('**Display Raw Data**'):
    st.dataframe(data, use_container_width=True)
