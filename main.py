import streamlit as st
import plotly.express as px
import pandas as pd
from streamlit_login_auth_ui.widgets import __login__
from streamlit_login_auth_ui.mydeta import deta_db
from streamlit_option_menu import option_menu
from deta import Deta


st.set_page_config(
    page_title="Health Care",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Store health records in deta base.
deta = Deta(st.secrets["Deta_Project_Key"])
dbhealth = deta.Base(st.secrets["Deta_Db_Health"])


def bp_reading(systolic, diastolic):
    """
    source: https://www.healthline.com/health/high-blood-pressure-hypertension/blood-pressure-reading-explained#danger-zone
    """
    # normal
    if systolic < 120 and diastolic < 80:
        return 'normal'
    # elevated
    elif systolic >= 120 and systolic <= 129 and diastolic < 80:
        return 'elevated'
    # hbps1 - high blood pressure stage 1
    elif (systolic >= 130 and systolic <= 139) or (diastolic >= 80 and diastolic < 89):
        return 'hbps1'
    # hbps2 - high blood pressure stage 2
    elif systolic >= 140 or diastolic >= 90:
        return 'hbps2'
    # hypertensive crisis
    elif systolic >= 180 or diastolic > 80:
        return 'hypertensive crisis'
    else:
        return 'undefined'


@st.experimental_memo(ttl=60)
def get_df(name):
    """Fetches data from deta."""
    df = pd.DataFrame()
    res = dbhealth.fetch()
    all_items: list[dict] = res.items
    if len(all_items):
        df = pd.DataFrame(all_items)
        df = df.sort_values(by=['Date'])
        df = df.loc[df.Name == name]
    return df


def get_figures(name):
    df = get_df(name)
    if len(df):
        df['DateTime'] = pd.to_datetime(df['Date'])
        df['Interpret'] = df.apply(lambda row: bp_reading(row.Systolic, row.Diastolic), axis = 1)

        df_wide = df
        df_long=pd.melt(df_wide, id_vars=['DateTime'], value_vars=['Systolic', 'Diastolic'])

        fig = px.line(df_long, x='DateTime', y='value', color='variable', markers=True, text='value', height=400)
        fig.update_layout(
            margin=dict(l=50, r=10, t=70, b=50),
            title_text=f"{name.title()}'s BP", title_x=0.5, title_y=0.9,
            legend=dict(
                x=0.01,
                y=0.98,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                    color="black"
                ),
            )
        )
        fig.update_traces(connectgaps=True, textposition="top center")
        fig.update_xaxes(
            dtick="D1",
            tickformat="%y-%m-%d",
        )


        # fig2
        df_wide = df
        df_long=pd.melt(df_wide, id_vars=['DateTime'], value_vars=['Interpret'])

        fig2 = px.line(df_long, x='DateTime', y='value', color='variable', markers=True, text='value',
                       height=400,
                       color_discrete_sequence=["#ff97ff"])
        fig2.update_layout(
            margin=dict(l=50, r=10, t=70, b=50),
            title_text="Interpretation", title_x=0.5, title_y=0.9,
            legend=dict(
                x=0.01,
                y=0.98,
                traceorder="normal",
                font=dict(
                    family="sans-serif",
                    size=12,
                    color="black"
                ),
            )            
        )
        fig2.update_traces(connectgaps=True, textposition="top center")
        fig2.update_xaxes(
            dtick="D1",
            tickformat="%y-%m-%d",
        )

        return df, fig, fig2

    return None, None, None


def show_plots(df, fig, fig2):
    st.plotly_chart(fig, use_container_width=True, theme=None, height=400)
    st.plotly_chart(fig2, use_container_width=True, theme=None, height=400)

    dfs = df.drop(['Date', 'key'], axis=1)
    dfs = dfs.reset_index(drop=True)

    with st.expander('History', expanded=False):
        st.markdown(f'''
        <center><strong>History</strong></center>
        ''',unsafe_allow_html=True)
        st.dataframe(dfs, use_container_width=True)

        st.markdown(f'''
        Source of [Interpretation](https://www.healthline.com/health/high-blood-pressure-hypertension/blood-pressure-reading-explained#danger-zone)
        ''', unsafe_allow_html=True)

    with st.expander('Legend', expanded=False):
        df_legend = get_legend()
        st.markdown(f'''
        <center><strong>Legend</strong></center>
        ''',unsafe_allow_html=True)
        st.dataframe(df_legend, use_container_width=True)


@st.experimental_memo(ttl=600)
def get_legend():
    legend = {
        'name': ['normal', 'elevated', 'hbps1', 'hbps2', 'hypertensive crisis'],
        'meaning': ['normal', 'elevated', 'high blood pressure stage 1',
                    'high blood pressure stage 2', 'hypertensive crisis']
    }
    return pd.DataFrame(legend)


def save_input(name):
    dt = st.session_state.mydate.strftime('%Y-%m-%d')
    tt = st.session_state.mytime.strftime('%H:%M:%S')
    date_ = f'{dt} {tt}'
    try:
        dbhealth.insert(
            {
                'Date': date_,
                'Systolic': st.session_state.mysystolic,
                'Diastolic': st.session_state.mydiastolic,
                'Name': name
            }
        )
    except Exception as exc:
        st.error(f'Data is not saved: {exc}')
    else:
        # print('Date is successfully saved!')
        st.success('Data is successfully saved!')


def main():
    db = None
    users_auth_file = '_secret_auth_.json'
    auth_token = 'courier_auth_token'

    deta_project_key = st.secrets['Deta_Project_Key']
    deta_db_name = st.secrets['Deta_Db_Name']
    db = deta_db(deta_project_key, deta_db_name)

    auth_token = st.secrets['courier_auth_token']

    cookie_password = st.secrets['cookie_password']

    __login__obj = __login__(
        auth_token=auth_token,
        company_name="Health Care",
        width=200,
        height=250,
        logout_button_name='Logout',
        hide_menu_bool=False,
        hide_footer_bool=False,
        lottie_url='https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json',
        users_auth_file=users_auth_file,
        is_disable_login=False,
        detadb=db,
        is_only_login=True,
        cookie_password=cookie_password)

    is_logged_in = __login__obj.build_login_ui()

    if is_logged_in:
        username = __login__obj.get_username()

        with st.sidebar:
            selected = option_menu("Main Menu", ["Home", 'Health'], 
                icons=['house', 'bookmark-heart'], menu_icon="cast", default_index=0)

        if selected == 'Home':
            col = st.columns([2, 3])
            with col[1]:
                st.markdown('# Home')

        elif selected == 'Health':
            col = st.columns([2, 3])
            with col[1]:
                st.markdown('# Health')

            options = st.secrets['selection']
            name = st.sidebar.selectbox('select name', options)  # set this for entry

            if username.lower() == st.secrets['admin'].lower():
                with st.expander('Date entry', expanded=False):
                    with st.form('form', clear_on_submit=True):
                        st.date_input('date', key='mydate')
                        st.time_input('time', key='mytime')
                        st.number_input('systolic', 0, 200, 120, step=1, key='mysystolic')
                        st.number_input('diastolic', 0, 200, 80, step=1, key='mydiastolic')
                        is_save = st.form_submit_button('Save')
                        if is_save:
                            save_input(name)

            if name == st.secrets['abc']:
                df, fig, fig2 = get_figures(name)
                if df is not None:
                    show_plots(df, fig, fig2)

            elif name == st.secrets['abd']:
                df, fig, fig2 = get_figures(name)
                if df is not None:
                    show_plots(df, fig, fig2)


if __name__ == '__main__':
    main()
