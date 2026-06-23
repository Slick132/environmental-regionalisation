window.REGION_OVERLAY = {
  "img": "figures/region_overlay.png",
  "bounds": [
    [
      -31.2349,
      26.2583
    ],
    [
      -21.91915,
      33.0295
    ]
  ],
  "center": [
    -26.57702,
    29.6439
  ],
  "legend": [
    {
      "k": 0,
      "color": "#1f77b4",
      "name": "Region 1",
      "n": 1329,
      "lat": -22.9919,
      "lon": 29.1363
    },
    {
      "k": 1,
      "color": "#ff7f0e",
      "name": "Region 2",
      "n": 2088,
      "lat": -27.1596,
      "lon": 30.7104
    },
    {
      "k": 2,
      "color": "#2ca02c",
      "name": "Region 3",
      "n": 1947,
      "lat": -24.8472,
      "lon": 29.3339
    },
    {
      "k": 3,
      "color": "#d62728",
      "name": "Region 4",
      "n": 1787,
      "lat": -28.5468,
      "lon": 31.6044
    },
    {
      "k": 4,
      "color": "#9467bd",
      "name": "Region 5",
      "n": 2676,
      "lat": -23.8836,
      "lon": 30.9592
    },
    {
      "k": 5,
      "color": "#8c564b",
      "name": "Region 6",
      "n": 1990,
      "lat": -27.2834,
      "lon": 29.6184
    },
    {
      "k": 6,
      "color": "#e377c2",
      "name": "Region 7",
      "n": 1481,
      "lat": -24.2148,
      "lon": 27.6135
    },
    {
      "k": 7,
      "color": "#7f7f7f",
      "name": "Region 8",
      "n": 893,
      "lat": -29.9071,
      "lon": 29.7304
    }
  ],
  "variables": {
    "temperature": {
      "img": "figures/overlay_temperature.png",
      "label": "Temperature",
      "unit": "&deg;C",
      "vmin": 15.92,
      "vmax": 23.73,
      "stops": [
        "#313695",
        "#588cc0",
        "#a3d3e6",
        "#e9f6e8",
        "#fee99d",
        "#fca55d",
        "#e34933",
        "#a50026"
      ],
      "regions": [
        {
          "k": 0,
          "value": 22.65,
          "color": "#e34933"
        },
        {
          "k": 1,
          "value": 18.65,
          "color": "#a3d3e6"
        },
        {
          "k": 2,
          "value": 19.81,
          "color": "#e9f6e8"
        },
        {
          "k": 3,
          "value": 22.51,
          "color": "#fee99d"
        },
        {
          "k": 4,
          "value": 23.73,
          "color": "#a50026"
        },
        {
          "k": 5,
          "value": 17.72,
          "color": "#588cc0"
        },
        {
          "k": 6,
          "value": 22.58,
          "color": "#fca55d"
        },
        {
          "k": 7,
          "value": 15.92,
          "color": "#313695"
        }
      ]
    },
    "precipitation": {
      "img": "figures/overlay_precipitation.png",
      "label": "Precipitation",
      "unit": "mm",
      "vmin": 366,
      "vmax": 886,
      "stops": [
        "#e6f5b2",
        "#bbe4b5",
        "#76cabc",
        "#3db2c4",
        "#1d8dbe",
        "#225ca7",
        "#243392",
        "#081d58"
      ],
      "regions": [
        {
          "k": 0,
          "value": 366,
          "color": "#e6f5b2"
        },
        {
          "k": 1,
          "value": 886,
          "color": "#081d58"
        },
        {
          "k": 2,
          "value": 623,
          "color": "#3db2c4"
        },
        {
          "k": 3,
          "value": 805,
          "color": "#225ca7"
        },
        {
          "k": 4,
          "value": 596,
          "color": "#76cabc"
        },
        {
          "k": 5,
          "value": 754,
          "color": "#1d8dbe"
        },
        {
          "k": 6,
          "value": 518,
          "color": "#bbe4b5"
        },
        {
          "k": 7,
          "value": 825,
          "color": "#243392"
        }
      ]
    },
    "humidity": {
      "img": "figures/overlay_humidity.png",
      "label": "Humidity",
      "unit": "%",
      "vmin": 54.4,
      "vmax": 74.4,
      "stops": [
        "#e0f3f5",
        "#c4e9e1",
        "#92d5c4",
        "#62c09f",
        "#3fab72",
        "#218944",
        "#006c2c",
        "#00441b"
      ],
      "regions": [
        {
          "k": 0,
          "value": 59.02,
          "color": "#92d5c4"
        },
        {
          "k": 1,
          "value": 66.73,
          "color": "#218944"
        },
        {
          "k": 2,
          "value": 58.76,
          "color": "#c4e9e1"
        },
        {
          "k": 3,
          "value": 74.4,
          "color": "#00441b"
        },
        {
          "k": 4,
          "value": 67.41,
          "color": "#006c2c"
        },
        {
          "k": 5,
          "value": 61.17,
          "color": "#62c09f"
        },
        {
          "k": 6,
          "value": 54.4,
          "color": "#e0f3f5"
        },
        {
          "k": 7,
          "value": 66.7,
          "color": "#3fab72"
        }
      ]
    },
    "wind": {
      "img": "figures/overlay_wind.png",
      "label": "Wind",
      "unit": "m/s",
      "vmin": 1.808,
      "vmax": 3.585,
      "stops": [
        "#ebe9f3",
        "#d5d5e9",
        "#b8b8d9",
        "#9b97c6",
        "#7e79b8",
        "#694fa2",
        "#53268f",
        "#3f007d"
      ],
      "regions": [
        {
          "k": 0,
          "value": 3.585,
          "color": "#3f007d"
        },
        {
          "k": 1,
          "value": 1.808,
          "color": "#ebe9f3"
        },
        {
          "k": 2,
          "value": 2.144,
          "color": "#b8b8d9"
        },
        {
          "k": 3,
          "value": 2.638,
          "color": "#53268f"
        },
        {
          "k": 4,
          "value": 2.615,
          "color": "#7e79b8"
        },
        {
          "k": 5,
          "value": 2.604,
          "color": "#9b97c6"
        },
        {
          "k": 6,
          "value": 2.623,
          "color": "#694fa2"
        },
        {
          "k": 7,
          "value": 2.07,
          "color": "#d5d5e9"
        }
      ]
    }
  }
};
