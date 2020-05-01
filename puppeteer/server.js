'use strict';
const express = require('express');
const bodyParser =require("body-parser");
const fun = require('./spiders/airfrance')
const server = express();
//const port = 3000;
server.use(bodyParser.json());
// Add headers
server.use(function (req, res, next) {
    // Website you wish to allow to connect
    res.setHeader('Access-Control-Allow-Origin', 'http://localhost:5000');
    // Request methods you wish to allow
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, PATCH, DELETE');
    // Request headers you wish to allow
    res.setHeader('Access-Control-Allow-Headers', 'X-Requested-With,content-type');
    // Set to true if you need the website to include cookies in the requests sent
    // to the API (e.g. in case you use sessions)
    res.setHeader('Access-Control-Allow-Credentials', true);
    next();
});
server.post('/airfrance', async function(req, res){
    let responce= await fun.franceAirline(req.body)
    res.send(responce)
});
const PORT = process.env.PORT || 5000;
server.listen(PORT, () => {
  console.log(`app running on port ${PORT}`);
});