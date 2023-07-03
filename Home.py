import streamlit as st
import pandas as pd
import plotly.figure_factory as ff

st.set_page_config(page_title="Home",
                   page_icon="🏡",
                   layout='wide',
                   menu_items={"Get help": "https://github.com/Norris-Wang/Taxi_Visualization"})

st.write('# Taxi Pick-up And Drop-off Analysis 🚕')
st.caption('In this app, you can upload a taxi data file to analyze it in multiple dimensions.')


@st.cache_data(persist="disk")
def Load_Data_From_File(file):
    if not file:
        st.warning('File not delected!')
        st.stop()
    data = pd.read_csv(file, header=None)
    data.columns = ['ID', 'GetOnTime', 'GetOnLon', 'GetOnLat', 'GetOffTime', 'GetOffLon', 'GetOffLat', 'Duration']
    return data

try:
    data = st.session_state['data']
except (AttributeError, NameError, KeyError):
    # 输入数据
    file = st.file_uploader('**Select a file**', type=['txt', 'csv'])
    data = Load_Data_From_File(file)

Record_Num = data.shape[0]              # 记录数
ID_list = list(set(data.ID.values))     # 出租车编号列表
Taxi_Num = len(ID_list)                 # 出租车数
Min_Duration = data['Duration'].min()//60
Max_Duration = data['Duration'].max()//60
st.session_state['data'] = data
st.session_state['ID_list'] = ID_list
st.session_state['Min_Duration'] = Min_Duration
st.session_state['Max_Duration'] = Max_Duration

st.divider()

# 统计信息
st.header('**Statistics** 📊')
st.caption('You can grasp the orders and query the records \
           of different taxis here.')
st.write('In the file you uploaded, there are ', Record_Num, ' items, containing ', Taxi_Num, ' different taxis.')

st.write('The table below shows the **basic statistic information** \
         of the distribution of the number of the orders.')
Taxi_Group = pd.DataFrame(data.ID.value_counts()).reset_index()
Taxi_Group.columns = ['ID', 'Orders']
description = pd.DataFrame(Taxi_Group.Orders.describe()).T
Min_Num = int(description['min'].values[0])
Max_Num = int(description['max'].values[0])
st.dataframe(description.iloc[:,1:], use_container_width=True)
st.caption('*std* -- Standard Deviation')
st.caption('*25%, 50%, 75%* -- first, second and third quantiles')

# 显示各出租车载客量直方图
def Draw_Orders(data):
    denseplot = ff.create_distplot(
        [list(data.Orders)], 
        group_labels=['Number of Orders'], 
        bin_size=.5,
        rug_text=[list(data.ID)])
    st.plotly_chart(denseplot, use_container_width=True)


st.subheader('Histogram of Taxi')
st.write("Then, let's take a look at the distribution visually.")

# 异常值过滤
if st.checkbox(label='Remove the anormaly'):
    anormaly_min, anormaly_max = st.select_slider(
        label='Select the bound beyond which you regard the anormaly is',
        options=sorted(list(set(Taxi_Group.Orders.values))),
        value=(Min_Num, Max_Num))
    normal_TaxiGroup = Taxi_Group[(Taxi_Group.Orders>=anormaly_min) &
                               (Taxi_Group.Orders<=anormaly_max)]
    Draw_Orders(normal_TaxiGroup)
else:
    Draw_Orders(Taxi_Group)

st.write('In the graph, you can see a curve and many bars above \
         and a set of vertical dashes below. The bars show \
         the frequency of different number of orders while \
         the curve is the probability density function. \
         And Each dash represents a record of a taxi and \
         its number of orders. You can zoom in and hold your mouse \
         on the curve and dashes to see the data.')

# 查询指定出租车的运行情况
with st.expander('**Taxi Query**'):
    tab1, tab2 = st.tabs(tabs=['By ID', 'By Number of Orders'])
    with tab1:
        taxi_filter = st.number_input(
            label='**Input a taxi ID** 🆔',
            value=0,
            help='Query data of a specified taxi based on its ID')
        filted_data = data[data.ID==taxi_filter]
        st.write(filted_data.shape[0], 'record(s) are found')
        st.dataframe(filted_data, 
                     use_container_width=True, 
                     hide_index=True)
    with tab2:
        Lower_Bound, Upper_Bound = st.select_slider(
            label='**Drag the button to select a range**',
            help='Query data of some specified taxis base on their number of orders',
            options=sorted(list(set(Taxi_Group.Orders.values))),
            value=(Min_Num, Max_Num))
        filted_TaxiGroup = Taxi_Group.query('@Upper_Bound>@Taxi_Group.Orders>@Lower_Bound ')
        st.write(filted_TaxiGroup.shape[0], 'record(s) are found')
        st.dataframe(filted_TaxiGroup.T)

st.divider()

st.write('For advanced analysis, please **click the items** in the sidebar** at the top left corner.')

if st.checkbox('**Display Raw Data**'):
    st.dataframe(data)
