from flask import Flask
from sqlalchemy import create_engine, text
import os
import json

app = Flask(__name__)


@app.route('/api/')
def hello_world():
    engine = create_engine(f"sqlite+pysqlite:///{os.path.dirname(os.path.realpath(__file__))}/inverter.db", future=True)
    with engine.connect() as conn:
        result = conn.execute(text("select strftime('%H:%M', datetime(min(register_history.date_created), 'localtime')) as hour, min(state) as min, max(state) as max, round(avg(state), 0) as mean, datetime(min(register_history.date_created), 'localtime') as from_datetime, datetime(max(register_history.date_created), 'localtime') as to_datetime from registers left join register_history on id = register_id and register_history.date_created > date() and register_history.state > 0 where name = 'current_generation' group by strftime('%Y-%m-%d %H', register_history.date_created) || cast(strftime(' %M', register_history.date_created)/10 as int)"))
        
        history_min = {'x': [], 'y': []}
        history_avg = {'x': [], 'y': []}
        history_max = {'x': [], 'y': []}
        for hours in result.all():
            history_min['x'].append(hours.hour)
            history_min['y'].append(hours.min)
            history_avg['x'].append(hours.hour)
            history_avg['y'].append(hours.mean)
            history_max['x'].append(hours.hour)
            history_max['y'].append(hours.max)
            
        return json.dumps({'min': history_min, 'avg': history_avg, 'max': history_max})


if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
