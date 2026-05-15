import { createApp } from 'vue'
import 'vant/lib/index.css'
import {
  Field, List, Cell, Button, NavBar, Tabs, Tab
} from 'vant'
import App from './App.vue'

const app = createApp(App)
app.use(Field)
app.use(List)
app.use(Cell)
app.use(Button)
app.use(NavBar)
app.use(Tabs)
app.use(Tab)
app.mount('#app')
