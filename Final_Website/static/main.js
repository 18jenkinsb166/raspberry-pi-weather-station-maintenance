let boldBlack = "rgba(0,0,0,1)";
let faintBlack = "rgba(0,0,0,0.2)";
let connectingOrange = "rgb(254, 141, 2)";
let connectedGreen = "rgb(4, 167, 40)"
let disconnectedRed = "rgb(205, 25, 50)"
let timeBeforeInactive = 2 // mins 



async function get_all_json_data() {
    let response = await fetch("http://127.0.0.1:5000/data");
    let data = response.json()
    return data;
}
window.addEventListener('load', function() {
    get_all_json_data()
        .then(data => load_page(data))

    $(window).resize(resizeFunc());
});




function load_page(jsondata) {

    let tempData = []
    let rainData = []
    let pressureData = []
    let windSpeedData = []
    let humidityData = []
    let windDirectionData = []
    let dayTypeData = []
    let timeStampData = []

    jsondata.forEach(dataset => {
        tempData.push(dataset['temperature'])
        rainData.push(dataset['precipitation'])
        pressureData.push(dataset['pressure'])
        windSpeedData.push(dataset['wind_speed'])
        humidityData.push(dataset['humidity'])
        windDirectionData.push(dataset["wind_direction"])
        dayTypeData.push(dataset["day_type"])
        timeStampData.push(dataset["time_stamp"])
    });



    // create readout boxes
    let tempReadOutBox = new Dataset("Temperature", "°C", "readout-box-temp", tempData);
    let pressureReadOutBox = new Dataset("Pressure", "mb", "readout-box-pressure", pressureData);
    let humidityReadOutBox = new Dataset("Humidity", "%", "readout-box-humidity", humidityData);
    let rainReadOutBox = new Dataset("Rain", "mm", "readout-box-rain", rainData);
    let windSpeedReadOutBox = new Dataset("Wind Speed", "mph", "readout-box-wind", windSpeedData);

    // main graph on page 3
    let bigGraph = new Graph('Temp', 'graph-graph-big', tempData, timeStampData, "°C", boldBlack, faintBlack, true)



    // buttons on page 3
    let tempButton = document.getElementById("temp-button-big-graph");
    let pressureButton = document.getElementById("pressure-button-big-graph");
    let rainButton = document.getElementById("rain-button-big-graph");
    let windButton = document.getElementById("wind-button-big-graph");
    let humidButton = document.getElementById("humid-button-big-graph");

    let buttons = [tempButton, pressureButton, rainButton, windButton, humidButton]
    page3Buttons(buttons, bigGraph, jsondata); // adds functionality to each button, and the big graph 

    boolConnected = isConnected(timeStampData[timeStampData.length - 1])
    connectingButton(boolConnected)
    updateBGimg(tempReadOutBox, rainReadOutBox); // adds background img
    sandringhamLogo(); // adds sandinrgham logo img
    selfieImg(); // adds selfie img 
    piImg(); // adds the pi img 
    lastUpdatedAt(timeStampData[timeStampData.length - 1]); // adds the "last updated" first page

}


class Dataset {
    constructor(title, unit, divName, data) {
        this.title = title;
        this.unit = unit;
        this.divName = divName;
        this.data = data;
        this.editReadOut();
    }


    editReadOut() {
        this.currentData = this.data[0]; // shows the first element in readout box 
        this.div = document.getElementById(this.divName);
        this.child = this.div.getElementsByTagName("p");

        // Add spacing between unit and value for some data series
        if (this.unit == "°C" || this.unit == "%") {
            this.child[0].innerText = this.currentData + this.unit;
        } else {
            this.child[0].innerText = this.currentData + " " + this.unit;
        }

    }


}

class Graph {
    constructor(title, id, data, timestamps, unit, rgbaFront, rgbaBack, slider = false) {
            this.title = title
            this.backgroundColour = rgbaFront
            this.colour = rgbaFront
            this.borderColour = rgbaBack
            this.ctx = document.getElementById(id).getContext('2d')
            this.data = data;
            this.dataBeingUsed = this.data
            this.timeStamps = timestamps
            this.unit = unit;
            this.xlabels = this.createXlabels(timestamps)
            this.initialiseGraph(unit)
            if (slider == true) {
                this.initialiseSlider();
            }

        }
        // creates slider below graph 
    initialiseSlider() {
        this.sliders = document.getElementsByClassName("slider-big-graph"); // only lets you take as a list
        this.slider = this.sliders[0] // one element array
        this.slider.max = this.data.length;
        this.slider.value = this.slider.max;
        this.slider.addEventListener("input", () => { this.editDisplayData() });
        this.editDisplayData();
    }

    //  creates the graph 
    initialiseGraph(unit) {
        this.chart = new Chart(this.ctx, {
                type: 'line',
                data: {
                    labels: this.xlabels,
                    datasets: [{
                        label: this.title,
                        data: this.dataBeingUsed,
                        backgroundColor: this.backgroundColour,
                        color: this.colour,
                        borderColor: this.borderColour

                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value, index, ticks) {
                                    value = value + " " + unit;
                                    return value;
                                }
                            }
                        }
                    },
                    responsive: true,
                    interaction: {
                        intersection: false,
                    }
                }
            }

        );
    }

    // adds the dates to the x axis of the graph 
    createXlabels() {
        let xlabels = [] // local variable
        for (let dayCounter = 1; dayCounter <= this.dataBeingUsed.length; dayCounter++) {
            xlabels.push(this.timeStamps[dayCounter - 1])
        }

        return xlabels
    }

    // uses the slider to determine how much of the data should be shown 
    editDisplayData() {
        let val = this.slider.value;


        this.dataBeingUsed = this.data.slice(0, val); // edits which part of data set is shwon
        this.xlabels = this.createXlabels()


        this.chart.data.datasets.forEach((dataset) => {
            dataset.data = this.dataBeingUsed;
        })
        this.chart.data.labels = this.xlabels;
        this.chart.update()
    }
}


// Update the background image to the current weather

function updateBGimg(tempReadOutBox, rainReadOutBox) {
    //console.log(tempReadOutBox.currentData);
    var date = new Date();
    var hours = date.getHours();

    // if (time <= 6 && time >= 18) {

    //     r.style.setProperty('--bgImg', "url('../images/night.png')");
    // } else {
    //     if (rainReadOutBox.currentData > 0) {
    //         r.style.setProperty('--bgImg', "url('../images/rain.png')");
    //     } else {
    //         if (tempReadOutBox.currentData > 20) {

    //             r.style.setProperty('--bgImg', "url('../images/sunny.png')");
    //         } else if (tempReadOutBox.currentData > 14) {
    //             r.style.setProperty('--bgImg', "url('../images/mild.png')");
    //         } else {
    //             r.style.setProperty('--bgImg', "url('../images/cold.png')");
    //         }
    //     }
    // }
    let evening_hour = 20;
    let morning_hour = 8;
    let rain_threshold = 0;
    let sunny_temp_threshold = 20;
    let cold_temp_threshold = 10;
    let img_file = "";

    if (tempReadOutBox.currentData > sunny_temp_threshold) {
        img_file = "sunny"
    }

    if (tempReadOutBox.currentData < cold_temp_threshold) {
        img_file = "cold";
    }

    if (hours < morning_hour) {
        img_file = "night"
    }

    if (hours > evening_hour) {
        img_file = "night"
    }

    if (rainReadOutBox.currentData > rain_threshold) {
        img_file = "rain"
    }

    fetch(`http://127.0.0.1:5000/images/${img_file}`)
        // .then(response => console.log(response))
        .then(img => {
            var r = document.getElementsByClassName('intro')[0];
            r.style.setProperty('background-image', `url(${img['url']})`);
        })
}

// returns sandringham logo img and sets to div in top left 
function sandringhamLogo() {
    fetch("http://127.0.0.1:5000/images/logo")
        .then(img => {
            var logoImg = document.getElementById("sand-logo")
            logoImg.src = img['url']
        })
}

// returns selfie img and sets to about section 
function selfieImg() {
    fetch("http://127.0.0.1:5000/images/selfie")
        .then(img => {
            var selfieImg = document.getElementById("selfie-img")
            selfieImg.src = img['url']
        })
}

function piImg() {
    fetch("http://127.0.0.1:5000/images/raspberry")
        .then(img => {
            var piImg = document.getElementById("pi-img")
            piImg.src = img['url']
        })
}

// changes the graph data upon click of the dropdown 
function dropdownFunctionality(value, bigGraph, jsondata) {
    if (value == "Temperature") {
        unit = "°C"
        filter = "temperature"
    } else if (value == "Pressure") {
        unit = "Pa"
        filter = "pressure"
    } else if (value == "Rain") {
        unit = "mm"
        filter = "precipitation"
    } else if (value == "Wind Speed") {
        unit = "mph";
        filter = "wind_speed"
    } else if (value == "Humidity") {
        unit = "%";
        filter = "humidity"
    }
    let newdata = [];
    jsondata.forEach(dataset => {
        newdata.push(dataset[filter])
    });

    // bigGraph.data = [4,3,2,1,2,4,5,6,6,4];

    bigGraph.chart.data.datasets.forEach((dataset) => {
        dataset.data = newdata; // changes the data
        dataset.label = value; // changes the title
    })

    bigGraph.data = newdata;
    // bigGraph.chart.data.datasets.label = dropdown.target.value;

    bigGraph.xlabels = bigGraph.createXlabels()
    bigGraph.chart.data.labels = this.xlabels;
    bigGraph.initialiseSlider();
    bigGraph.chart.options.scales.y.ticks.callback = function(value, index, ticks) {
        value = value + " " + unit;
        return value
    }
    bigGraph.chart.update()
}

// checks which button is clicked, and toggles the required classes 
function page3Buttons(buttons, bigGraph, jsondata) {

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            //removes selected from all
            buttons.forEach((button) => {
                button.classList.remove("selected-button")
            });
            button.classList.toggle("active")

            // changes the graph
            dropdownFunctionality(button.innerText, bigGraph, jsondata)

            // makes the button selected
            button.classList.add("selected-button");
        })

    });

}

// edits the "last updated at" on the first page 
function lastUpdatedAt(time) {
    elm = document.getElementsByClassName('last-updated')[0];
    elm.innerText = `Last Updated: ${time}`
}

function connectingButton(boolConnected) {
    statusText = document.getElementsByClassName("status-text")[0]
    statusDot = document.getElementsByClassName("status-dot")[0]
    statusText.style.color = connectingOrange;
    statusText.innerText = "Status: Connecting...";
    statusDot.style.animation = "connecting-dot 2s infinite";

    // set to green 
    if (boolConnected == true) {
        setTimeout(function() {
            statusText.style.color = connectedGreen;
            statusText.innerText = "Status: Connected";
            statusDot.style.animation = "dot-animation 2s infinite";
        }, 3000)
    } else {
        setTimeout(function() {
            statusText.style.color = disconnectedRed;
            statusText.innerText = "Status: Offline";
            statusDot.style.animation = "disconnected 2s infinite";
        }, 3000)
    }

    // set to red


}

function isConnected(recentTimeStamp) {
    console.log(recentTimeStamp);
    // currentTimeStamp = yyyy-mm-dd hh:mm:ss eg
    let today = new Date();
    let currentHours = today.getHours(); // 0 - 24 
    let currentMinutes = today.getMinutes() // 0 - 60
    let totalMinsCurrentTime = (currentHours * 60) + currentMinutes;

    let timeStampTime = recentTimeStamp.split(/\s+/)[1] // splits by a whitespace, in form hh:mm:ss
    let timeStampHours = timeStampTime.split(':') //[22, 30, 00], hh, mm, ss
    let totalMinsTimeStampTime = (timeStampHours[0] * 60) + timeStampHours[1]

    if (Math.abs(totalMinsCurrentTime - totalMinsTimeStampTime) > timeBeforeInactive) {
        return false
    } else {
        return true
    }
}


function resizeFunc() {
    if ($(window).width() < 650) {
        alert('Please view on a bigger screen!');
    }
    if ($(window).height() < 535) {
        alert("please view on a bigger screen!")
    }
}