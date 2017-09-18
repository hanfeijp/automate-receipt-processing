var url = require('url')
var fs = require('fs');
var http = require('http');
var process = require('process');
var execSync = require('child_process').execSync;

function user() { 
    return 'ebragge'; 
}

function imageName() {
    var time = process.hrtime();
    var name = '/home/' + user() + '/CTPN/demo_images/' + time[0].toString() + '_' + time[1].toString();
    return name;
}

function processPost(request, response, callback) {
    if(typeof callback !== 'function') return null;

    var queryData = new Buffer([]);

    if(request.method == 'POST') {
        request.on('data', function(data) {
            queryData = Buffer.concat([queryData, data]);
            if(queryData.length > 5e7) {
                response.writeHead(413, {'Content-Type': 'text/plain'});
                response.end();
                request.connection.destroy();
            }
        });

        request.on('end', function() {
            var fileName = imageName() + '.png';
            if(fs.existsSync(fileName)) fs.unlinkSync(fileName);

            fs.writeFile(fileName, queryData, { encoding: 'binary', mode: 0o777 },
                function(err) {
                    if(err) {
                        console.log(err);
                        callback(0);
                    } else {
                        callback(1, fileName);
                    }
            });
        });

    } else {
        response.writeHead(405, {'Content-Type': 'text/plain'});
        response.end();
    }
}

http.createServer(function(request, response) {
    if(request.method == 'GET') {
        var data = url.parse(request.url, true).query;
        var f = imageName();
        var loc = data.url;
        var res = '{ \"Lines\": 0 }';
        try {
            if (loc.indexOf('.jpg') != -1 || loc.indexOf(".png") != -1) {
                if (loc.indexOf('.jpg') != -1) f = f + ".jpg";
                else  f = f + ".png";

                if(fs.existsSync(f)) fs.unlinkSync(f);
                var cmd = "runuser -l " + user() + " -c '/anaconda/bin/python /home/" + user() + "/CTPN/tools/service.py " +  user() + " 1 " + loc + " " + f + "'"; 
                res = execSync(cmd, {silent: true}); 
            } 
        } catch (ex) {}

        if(fs.existsSync(f)) fs.unlinkSync(f);
        
        response.writeHead(200, "OK", {"Content-Type": "application/json"});
        response.write(res);
        response.end();
    }
    else if(request.method == 'POST') {

        processPost(request, response, function(ok, f) {
            var res = '{ \"Lines\": 0 }';
            if (ok) {
                try {
                    var cmd = "runuser -l " + user() + " -c '/anaconda/bin/python /home/" + user() + "/CTPN/tools/service.py " +  user() + " 0 " + f + "'";
                    res = execSync(cmd, {silent: true});
                } catch (ex) {}

                if(fs.existsSync(f)) fs.unlinkSync(f);
            }
            
            response.writeHead(200, "OK", {"Content-Type": "application/json"});
            response.write(res);
            response.end();
        });
    } else {
        response.writeHead(200, "OK", {'Content-Type': 'text/plain'});
        response.end();
    }

}).listen(80);

console.log("Server is listening");
