let connectingOrange = "rgb(254, 141, 2)"; // colour of the dot on the first page whilst connecting
let connectedGreen = "rgb(4, 167, 40)" // colour of the dot on the first page if connected
let disconnectedRed = "rgb(205, 25, 50)" // colour of the dot on the first page if not connected 
let timeBeforeInactive = 6 // this is used to determine if the server is connected. Time in hours at which it determines that the server is offline.

// "python server/server.py" put in terminal without speech marks - make sure that your root directory is correct
// website runs on local host... go here: http://127.0.0.1:5000/


// the main function that is run when the webpage has loaded
window.addEventListener('load', function() {
    get_all_json_data() // calls the function - function is written at the bottom 
        // it is called as a promise, and the ".then" block of code runs when the data has been returned. 
        .then(function(data) {
            load_page(data) // calls the function load page 
        })
    window.addEventListener("resize", resizeFunc);
    // this is an event listener. The function - resizeFunc is called any time the window is resized
    // this is so that we can check if the screen size is too small, and the error needs to be shown. 
});



// main function that gets called when page is loaded. 
// the full set of json data stored on the pi is passed as an argument 
function load_page(jsondata) {

    // empty arrays for the data
    let tempData = []
    let rainData = []
    let pressureData = []
    let windSpeedData = []
    let humidityData = []
    let windDirectionData = []

    // empty arrays for the time stamps
    let timeStampData = []

    // iterates through each reading of the data set and runs through the for loop with "dataset" as the variable 
    // that takes the value of each reading
    jsondata.forEach(dataset => {
        tempData.push(dataset['temperature'].toFixed(1)) // rounds to 1dp
        rainData.push(dataset['precipitation'].toFixed(2)) // rounds to 2dp 
        pressureData.push(Math.round(dataset['pressure'])) // rounds to nearest integer
        windSpeedData.push(Math.round(dataset['wind_speed'])) // rounds to nearest integer
        humidityData.push(Math.round(dataset['humidity'])) // rounds to nearest integer
        windDirectionData.push(Math.round(dataset["wind_direction"])) // rounds to nearest integer
        timeStampData.push(dataset["timestamp"])
    });



    colours = buttonAnimation(); // makes the graph a random colour upon first calling



    // create readout boxes
    let tempReadOutBox = new Dataset("Temperature", "°C", "readout-box-temp", tempData);
    let pressureReadOutBox = new Dataset("Pressure", "mb", "readout-box-pressure", pressureData);
    let humidityReadOutBox = new Dataset("Humidity", "%", "readout-box-humidity", humidityData);
    let rainReadOutBox = new Dataset("Rain", "mm", "readout-box-rain", rainData);
    let windSpeedReadOutBox = new Dataset("Wind Speed", "mph", "readout-box-wind", windSpeedData, windDirectionData[windDirectionData.length - 1]);

    // main graph on page 3
    let bigGraph = new Graph('Temp', 'graph-graph-big', tempData, timeStampData, "°C", colours[0], colours[1], true)



    // buttons on page 2
    let tempButton = document.getElementById("temp-button-big-graph");
    let pressureButton = document.getElementById("pressure-button-big-graph");
    let rainButton = document.getElementById("rain-button-big-graph");
    let windButton = document.getElementById("wind-button-big-graph");
    let humidButton = document.getElementById("humid-button-big-graph");

    let buttons = [tempButton, pressureButton, rainButton, windButton, humidButton]
    page3Buttons(buttons, bigGraph, jsondata, firstCall = true); // adds functionality to each button, and the big graph 

    boolConnected = isConnected(timeStampData[timeStampData.length - 1])
    connectingButton(boolConnected)

    getPhotoImages();
    lastUpdatedAt(timeStampData[timeStampData.length - 1]); // adds the "last updated" first page



}


class Dataset {
    constructor(title, unit, divName, data, windDirection = null) {
        this.title = title;
        this.unit = unit;
        this.divName = divName;
        this.data = data;
        this.windDirection = windDirection;

        this.editReadOut();
    }


    editReadOut() {
        this.currentData = this.data[this.data.length - 1]; // shows the first element in readout box 
        this.div = document.getElementById(this.divName);
        this.child = this.div.getElementsByTagName("p");

        // Add spacing between unit and value for some data series
        if (this.unit == "°C" || this.unit == "%") {
            this.child[0].innerText = this.currentData + this.unit;
        } else {
            this.child[0].innerText = this.currentData + " " + this.unit;
        }
        // getting rid of wind direction
        if (this.windDirection != null) {


            while (this.windDirection.toString().length != 3) {
                this.windDirection = "0" + this.windDirection
            }

            this.child[0].innerText = this.windDirection + '° ' + this.currentData + this.unit;

        }

    }


}

class Graph {
    constructor(title, id, data, timestamps, unit, rgbaFront, rgbaBack, slider_on = false) {
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

            if (slider_on == true) {
                this.initialiseSlider();
            }


        }
        // creates slider below graph 
    initialiseSlider() {
        this.sliders = document.getElementsByClassName("slider-big-graph"); // only lets you take as a list
        this.slider = this.sliders[0] // one element array
        this.slider.max = this.data.length;
        if (this.data.length >= 5) {
            this.slider.value = 5;
        };

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
                        borderColor: this.borderColour,
                        fill: false,

                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                autoSkip: true,
                                callback: function(value, index, ticks) {
                                    return value + " " + unit;
                                }

                            }

                        }
                    },

                    // interaction: {
                    //     intersection: false,
                    // },
                    // layout: {
                    //     padding: 50
                    // },
                    elements: {
                        line: {
                            tension: 0
                        }
                    }
                }
            }

        );
    }

    // adds the dates to the x axis of the graph 
    createXlabels() {
        // neeeds to be changed to show the right dates 
        let xlabels = [] // local variable
        for (let dayCounter = 1; dayCounter <= this.dataBeingUsed.length; dayCounter++) {
            xlabels.push(this.timeStamps[this.timeStamps.length - dayCounter])
        }
        xlabels.reverse()
        return xlabels
    }

    // uses the slider to determine how much of the data should be shown 
    editDisplayData() {
        let val = this.slider.value;

        // array of 10, if selected 1, we want from 9- 10 
        this.dataBeingUsed = this.data.slice(this.data.length - val, this.data.length); // edits which part of data set is shwon
        this.xlabels = this.createXlabels()

        console.log(this.xlabels.length)
        console.log(this.dataBeingUsed.length)


        this.chart.data.datasets.forEach((dataset) => {
            dataset.data = this.dataBeingUsed;
        })
        this.chart.data.labels = this.xlabels;
        this.chart.update()
    }
}

async function get_all_json_data() {
    let response = await fetch("/data");
    let data = response.json()
    return data;
}

function getPhotoImages() {
    updateBGimg();
    sandringhamLogo()
    selfieImg();
    piImg();
}

// Update the background image to the current weather
function updateBGimg() {


    fetch(`/background_image`)
        // .then(response => console.log(response))
        .then(img => {
            var r = document.getElementsByClassName('intro')[0];
            r.style.setProperty('background-image', `url(${img['url']})`);
        })
}

// returns sandringham logo img and sets to div in top left 
function sandringhamLogo() {
    fetch("/images/logo")
        .then(img => {
            var logoImg = document.getElementById("sand-logo")
            logoImg.src = img['url']
        })
}

// returns selfie img and sets to about section 
function selfieImg() {
    fetch("/images/selfie")
        .then(img => {
            var selfieImg = document.getElementById("selfie-img")
            selfieImg.src = img['url']
        })
}

function piImg() {
    fetch("/images/raspberry")
        .then(img => {
            var piImg = document.getElementById("pi-img")
            piImg.src = img['url']
        })
}

// changes the graph data upon click of the dropdown 
function dropdownFunctionality(value, bigGraph, jsondata, fgColour, bgColour) {
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


    bigGraph.chart.data.datasets.forEach((dataset) => {
        dataset.data = newdata; // changes the data
        dataset.label = value; // changes the title
        dataset.backgroundColor = fgColour
        dataset.color = fgColour
        dataset.borderColor = bgColour
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
function page3Buttons(buttons, bigGraph, jsondata, firstCall = false) {

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            //removes selected from all
            buttons.forEach((button) => {
                button.classList.remove("selected-button")
            });
            button.classList.toggle("active")



            // makes the button selected
            button.classList.add("selected-button");




            //  too allow random colour changing
            colours = buttonAnimation();

            // changes the groaph 
            dropdownFunctionality(button.innerText, bigGraph, jsondata, colours[0], colours[1])
                // bigGraph.initialiseGraph("mm")
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

    // currentTimeStamp = yyyy-mm-dd hh:mm:ss eg
    let today = new Date();

    let currentHours = today.getHours(); // 0 - 24 
    let currentDay = today.getDate(); // 1 - 31
    let currentMonth = parseInt(today.getMonth()) + 1; // 1 - 12
    let currentYear = today.getFullYear(); // 2022




    let timeStamp = recentTimeStamp.split(/\s+/)
    let timeStampTime = timeStamp[1] // splits by a whitespace, in form hh:mm:ss
    let timeStampYearMonthDay = timeStamp[0].split("-"); // splits in yyyy, mm, dd
    let timeStampHours = timeStampTime.split(':')[0]

    let timeStampYear = timeStampYearMonthDay[0];
    let timeStampMonth = timeStampYearMonthDay[1];
    let timeStampDay = timeStampYearMonthDay[2];

    let returnVal = true;

    if (currentYear != timeStampYear) { // compares years 
        returnVal = false;
        console.log('years')
    }
    if (currentMonth != timeStampMonth) { // compares months
        returnVal = false;
        console.log('mongth')
    }
    if (currentDay != timeStampDay) {
        returnVal = false;
        console.log('DAY')
    }
    if (currentHours < (parseInt(timeStampHours) + parseInt(timeBeforeInactive)) % 24) { // compares hours
        returnVal = false
        console.log('hours')
    }

    return returnVal;
}

function resizeFunc() {
    let all = document.getElementsByTagName("*");
    all = document.querySelectorAll("*")
    let error = document.getElementsByClassName("error")[0];


    if ($(window).width() < 700 || $(window).height() < 535) {
        all.forEach(element => {
            element.style.visibility = "hidden";
        });

        error.style.visibility = "visible";
        $(window).scrollTop(0);

    } else {
        all.forEach(element => {
            element.style.visibility = "visible";
        });

        error.style.visibility = "hidden";
        // $(window).scrollTop(0);
    }
}

function returnRandomHSL() {
    let max = 360
    let hue = Math.floor(Math.random() * max)
    var brightcolorname = `hsl(${hue}, 80%, 50%)`
    var dimcolorname = `hsl(${hue},40%,80%)`
    return [brightcolorname, dimcolorname]

}

function buttonAnimation() {
    colours = returnRandomHSL()

    nonSelectedButton = document.getElementsByClassName("drop-button-big-graph")

    for (let i = 0; i < nonSelectedButton.length; i++) {
        nonSelectedButton[i].style.background = 'linear-gradient(to right, rgba(169, 158, 158, 0.1) 50% ,' + colours[0] + ' 50%)'
        nonSelectedButton[i].style.backgroundSize = '200% 100%'
        nonSelectedButton[i].style.backgroundPosition = "left bottom"
            // nonSelectedButton[i].style.background = 'linear-gradient(to right, #000000, #ffffff)'

        nonSelectedButton[i].addEventListener('mouseover', function handleMouseOver() {
            if (nonSelectedButton[i].classList.contains("selected-button") == false) {
                nonSelectedButton[i].style.transition = "all 1s ease"
                nonSelectedButton[i].style.backgroundPosition = "right bottom"
            }
        });

        nonSelectedButton[i].addEventListener('mouseout', function handleMouseOut() {
            if (nonSelectedButton[i].classList.contains("selected-button") == false) {
                nonSelectedButton[i].style.background = 'linear-gradient(to right, rgba(169, 158, 158, 0.1) 50% ,' + colours[0] + ' 50%)'
                nonSelectedButton[i].style.backgroundSize = '200% 100%'
                nonSelectedButton[i].style.backgroundPosition = "left bottom"
            }
        });
    }
    selectedButton = document.getElementsByClassName("selected-button")[0]
    selectedButton.style.backgroundColor = colours[0]


    return colours
}