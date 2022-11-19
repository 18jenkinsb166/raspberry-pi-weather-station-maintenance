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



    // create readout boxes on the first page 
    let tempReadOutBox = new Dataset("Temperature", "°C", "readout-box-temp", tempData);
    let pressureReadOutBox = new Dataset("Pressure", "mb", "readout-box-pressure", pressureData);
    let humidityReadOutBox = new Dataset("Humidity", "%", "readout-box-humidity", humidityData);
    let rainReadOutBox = new Dataset("Rain", "mm", "readout-box-rain", rainData);
    let windSpeedReadOutBox = new Dataset("Wind Speed", "mph", "readout-box-wind", windSpeedData, windDirectionData[windDirectionData.length - 1]);

    // main graph on page 2
    let bigGraph = new Graph('Temp', 'graph-graph-big', tempData, timeStampData, "°C", colours[0], colours[1], true)



    // buttons on page 2
    let tempButton = document.getElementById("temp-button-big-graph");
    let pressureButton = document.getElementById("pressure-button-big-graph");
    let rainButton = document.getElementById("rain-button-big-graph");
    let windButton = document.getElementById("wind-button-big-graph");
    let humidButton = document.getElementById("humid-button-big-graph");

    // puts all buttons in a list to make them easier to work with
    // ig it's techically an array cus size doesnt change
    // altho if we're being really techincal JS would say it's a list 
    let buttons = [tempButton, pressureButton, rainButton, windButton, humidButton]
    page3Buttons(buttons, bigGraph, jsondata, firstCall = true); // adds functionality to each button, and the big graph 

    // adds functionality to the connecting button on the first page 
    boolConnected = isConnected(timeStampData[timeStampData.length - 1]) // function call 
    connectingButton(boolConnected) // function call 

    getPhotoImages(); // function call 
    // loads the images and puts them on the screen 

    lastUpdatedAt(timeStampData[timeStampData.length - 1]); // function call adds the "last updated" first page
    // this is the white text in the bottom left 



}

// class for each dataset - this is object oriented programming 

class Dataset {
    // constructor class is called when intilising object 
    constructor(title, unit, divName, data, windDirection = null) {
        this.title = title; // title of the readoutbox 
        this.unit = unit; // unit for the data of the readout box 
        this.divName = divName; // the name of the HTML div the readout box is in 
        this.data = data; // the list of all data values from the json data 
        this.windDirection = windDirection; // defaulted to null, but if wind speed, then it's passed as an extra parameter 

        // calls the editReadOut function below 
        this.editReadOut();
    }


    editReadOut() {
        // makes the acc changes to the readout boxes
        this.currentData = this.data[this.data.length - 1]; // most recent reading from the data 
        this.div = document.getElementById(this.divName); // identifies the html div for the readoutbox 
        this.child = this.div.getElementsByTagName("p"); // identifies the html p tag for the readout box


        // Add spacing between unit and value for some data series
        // Also adds the correct unit to the readout box p tag
        if (this.unit == "°C" || this.unit == "%") {
            this.child[0].innerText = this.currentData + this.unit;
        } else {
            this.child[0].innerText = this.currentData + " " + this.unit;
        }

        // getting rid of wind direction - only true if we're looking at the wind box 
        if (this.windDirection != null) {

            // adds 0s to the front of the wind bearing to make it more formal
            // this while loop caused me a lot of pain 
            while (this.windDirection.toString().length != 3) {
                this.windDirection = "0" + this.windDirection
            }

            // adds the wind direction to the paragraph text in the readout box 
            this.child[0].innerText = this.windDirection + '° ' + this.currentData + this.unit;

        }

    }


}

// OOP - for the big graph on the second page 
class Graph {
    // constructor class is called when an object of the class is intialised 
    constructor(title, id, data, timestamps, unit, rgbaFront, rgbaBack, slider_on = false) {
            this.title = title // graph title 
            this.colour = rgbaFront // main colour of the graph 
            this.ctx = document.getElementById(id).getContext('2d')
            this.backgroundColor = rgbaBack; // back colour of the line 
            this.data = data; // array for ALL the data 
            this.dataBeingUsed = this.data // specifically the subset of this.data representing the data currently being shown
            this.timeStamps = timestamps // array of the time stamps
            this.unit = unit; // unit for the graph 
            this.xlabels = this.createXlabels(timestamps) // function call that creates the x axis labels for the graph 
            this.defaultSliderValue = 5; // the value that the slider below the graph is set to by default - upon loading page

            this.initialiseGraph(unit) // function call - creates the graph 

            // creates slider below graph - function call 
            if (slider_on == true) {
                this.initialiseSlider();
            }



        }
        // creates slider below graph 
    initialiseSlider() {
        this.sliders = document.getElementsByClassName("slider-big-graph"); // returns one element array of the slider div from html
        this.slider = this.sliders[0] // turns array into variable
        this.slider.max = this.data.length; // sets the max value of the slider to the length of the data
        // makes sure that we have at least defualt size data readings 
        if (this.data.length >= this.defaultSliderValue) {
            // sets the defeault slider value to default value 
            this.slider.value = this.defaultSliderValue;
        };

        // adds event listener to slider
        // when the slider is clicked/ moved - editDisplayData function is called 
        this.slider.addEventListener("input", () => { this.editDisplayData() });
        // calls editDisplayData intially, to make sure it's set up right 
        this.editDisplayData();
    }

    //  creates the graph - see chart.js for documentation
    // this is an API 
    // https://www.chartjs.org
    initialiseGraph(unit) {
        this.chart = new Chart(this.ctx, {
                type: 'line',
                data: {
                    labels: this.xlabels,
                    datasets: [{
                        label: this.title,
                        data: this.dataBeingUsed,
                        color: this.colour, // changes the colour of the dots 
                        fill: false,
                        backgroundColor: this.colour, // the colour of the circle in the dot on the graph 
                        borderColor: this.backgroundColor // the colour of the line 

                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                autoSkip: true,
                                callback: function(value, index, ticks) {
                                    return value + " " + unit; // adds a space between unit and value - does this for all of them
                                }

                            }

                        }
                    },
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
        let xlabels = [] // local variable to store the date labels 
        for (let dayCounter = 1; dayCounter <= this.dataBeingUsed.length; dayCounter++) {
            xlabels.push(this.timeStamps[this.timeStamps.length - dayCounter])
        }
        // reverses the order of the data so that upon adding to the graph, it plots it in time order from left to right
        // this is because it comes from the server with the most recent reading being the "last" element in the array
        xlabels.reverse()
        return xlabels
    }

    // uses the slider to determine how much of the data should be shown 
    editDisplayData() {
        // val is set to the current value of the slider 
        let val = this.slider.value;

        // array of 10, if selected 1, we want from 9- 10 
        this.dataBeingUsed = this.data.slice(this.data.length - val, this.data.length); // edits which part of data set is shwon
        this.xlabels = this.createXlabels() // functiona call 

        // updates the graph to put the data point on 
        this.chart.data.datasets.forEach((dataset) => {
                dataset.data = this.dataBeingUsed;
            })
            // updates the x labels of the graph 
        this.chart.data.labels = this.xlabels;
        // calls the function to update the graph 
        this.chart.update()
    }
}

async function get_all_json_data() {
    // in built function in javascipt that requests the data 
    let response = await fetch("/data");
    let data = response.json()
    if(data.length == 0){
        alert("Some parts cannot be loaded as database contains no recent data (/data returned empty)")
    }
    return data;
}

function getPhotoImages() {
    // calls the functions that loads the images on the website - one image per function 
    updateBGimg();
    sandringhamLogo()
    selfieImg();
    piImg();
}

// Update the background image to the current weather
function updateBGimg() {
    // at the endpoint background image and puts it to the appropriate HTML element 
    fetch(`/background_image`)
        // .then(response => console.log(response))
        .then(img => {
            var r = document.getElementsByClassName('intro')[0];
            r.style.setProperty('background-image', `url(${img['url']})`);
        })
}

//  sandringham logo img and sets to div in top left 
function sandringhamLogo() {
    fetch("/images/logo")
        .then(img => {
            var logoImg = document.getElementById("sand-logo")
            logoImg.src = img['url']
        })
}

//  selfie img and sets to about section 
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
    // gets the appropriate data values in an array - newdata
    let newdata = [];
    jsondata.forEach(dataset => {
        newdata.push(dataset[filter])
    });

    // edits the values in the graph, the colour, the data, and the title. 
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
        value = value + " " + unit; // adds a space on the y axis between unit and data value. 
        return value
    }


    bigGraph.chart.update()
}

// checks which button is clicked, and toggles the required classes 
function page3Buttons(buttons, bigGraph, jsondata, firstCall = false) {

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            //removes selected from all- styling for buttons 
            buttons.forEach((button) => {
                button.classList.remove("selected-button")
            });
            button.classList.toggle("active")



            // makes the button selecteds
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
    // functionality for the connecting button on the first page. 
    statusText = document.getElementsByClassName("status-text")[0] // text that says "connecting..." or "online" or "offline"
    statusDot = document.getElementsByClassName("status-dot")[0] // the actual dot itself that changes colour 
    statusText.style.color = connectingOrange; // colour is at the top of the page as a global variable. 
    statusText.innerText = "Status: Connecting...";
    statusDot.style.animation = "connecting-dot 2s infinite"; // animation - see animation.css

    // set to green 
    if (boolConnected == true) {
        setTimeout(function() {
                statusText.style.color = connectedGreen;
                statusText.innerText = "Status: Connected";
                statusDot.style.animation = "dot-animation 2s infinite";
            }, 3000) // after 3 seconds it calls the connecting animation, and changes the text. 
    } else {
        setTimeout(function() {
                statusText.style.color = disconnectedRed;
                statusText.innerText = "Status: Offline";
                statusDot.style.animation = "disconnected 2s infinite";
            }, 3000) // after 3 seconds it calls the offline animation, and changes the text. 
    }




}

// this function basically compares the most recent data stamp to the current date and time 
function isConnected(mostRecentTimeStamp) {

    // currentTimeStamp = yyyy-mm-dd hh:mm:ss eg
    now = new Date()
    // Date.parse puts it in terms of ms since 1970 (general format) which is fed to the constructor
    then = new Date(Date.parse(mostRecentTimeStamp))
    // absolute diff in ms
    diff = now.getTime() - then.getTime()
    // 1000*7 ms in 7 min (added 2 min buffer)
    connected = diff <= 7000

    return connected
}


// checks the current size of the page and then adds the styles to all the elemnts to hide everything, and only show the error message 
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

// returns a random HSL colour for the graph, it returns a lighter and a darker one for the colour of the dots and the colour of the line
function returnRandomHSL() {
    let max = 360
    let hue = Math.floor(Math.random() * max)
    var brightcolorname = `hsl(${hue}, 80%, 50%)`
    var dimcolorname = `hsl(${hue},40%,80%)`
    return [brightcolorname, dimcolorname]

}

function buttonAnimation() { // buttons on the big graph page. 
    colours = returnRandomHSL() // function call 

    nonSelectedButton = document.getElementsByClassName("drop-button-big-graph")

    for (let i = 0; i < nonSelectedButton.length; i++) {
        nonSelectedButton[i].style.background = 'linear-gradient(to right, rgba(169, 158, 158, 0.1) 50% ,' + colours[0] + ' 50%)'
        nonSelectedButton[i].style.backgroundSize = '200% 100%'
        nonSelectedButton[i].style.backgroundPosition = "left bottom"


        nonSelectedButton[i].addEventListener('mouseover', function handleMouseOver() { // when mouse hover over 
            if (nonSelectedButton[i].classList.contains("selected-button") == false) {
                nonSelectedButton[i].style.transition = "all 1s ease"
                nonSelectedButton[i].style.backgroundPosition = "right bottom"
            }
        });

        nonSelectedButton[i].addEventListener('mouseout', function handleMouseOut() { // when mouse leaves the button hitbox 
            if (nonSelectedButton[i].classList.contains("selected-button") == false) {
                nonSelectedButton[i].style.background = 'linear-gradient(to right, rgba(169, 158, 158, 0.1) 50% ,' + colours[0] + ' 50%)'
                nonSelectedButton[i].style.backgroundSize = '200% 100%'
                nonSelectedButton[i].style.backgroundPosition = "left bottom"
            }
        });
    }
    selectedButton = document.getElementsByClassName("selected-button")[0]
    selectedButton.style.backgroundColor = colours[0] // changes the background colour of the button to the stronger version of the 2 random HSL colour buttons. 


    return colours
}