let xhr = new XMLHttpRequest();

xhr.responseType='';
xhr.onreadystatechange = () => {
    if (xhr.status == 200 && xhr.readyState == 4) {
        data = JSON.parse(xhr.responseText);
        var min = {
            x: data.min.x,
            y: data.min.y,
            mode: 'lines+markers',
            name: 'min',
            line: { shape: 'spline' },
            type: 'scatter'
        };

        var average = {
            x: data.avg.x,
            y: data.avg.y,
            mode: 'lines+markers',
            name: 'average',
            line: { shape: 'spline' },
            type: 'scatter'
        };

        var max = {
            x: data.max.x,
            y: data.max.y,
            mode: 'lines+markers',
            name: 'max',
            line: { shape: 'spline' },
            type: 'scatter'
        };


        var data = [min, average, max];

        var layout = {
            legend: {
                traceorder: 'reversed',
                font: { size: 16 },
                yref: 'paper'
            }
        };

        Plotly.newPlot('myDiv', data, layout);
    }

};

xhr.open('GET', '/api/');
xhr.send();
