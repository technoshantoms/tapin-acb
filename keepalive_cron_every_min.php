<?php
set_time_limit(59);

class Demon {
    const HOST = 'http://localhost:5000/';
    const FILE = 'lastnohupstart.unixtime';
    const EXPIRE = 60 * 2;
    
    public function writeStartTime() {        
        if(is_file(__DIR__ . '/' . static::FILE)) unlink (__DIR__ . '/' . static::FILE);
        file_put_contents(__DIR__ . '/' . static::FILE, time());
    }
    
    public function isExpiredByLastStartTime() {
        $lastStarted = (int) (is_file(__DIR__ . '/' . static::FILE) ? file_get_contents(__DIR__ . '/' . static::FILE) : 0);
        $lastStarted += static::EXPIRE;
        
        return $lastStarted < time();
    }
    
    public function isWorked() {        
        try {
            $response = file_get_contents(static::HOST);
            return !empty($response);
        } catch (Exception $ex) {}
        
        return false;
    }
}

class Process {    
    public function start($processName) {           
        try {            
$dir = '/home/wmbroker/opt/gateis_tapin/';
$cmd = "cd ".$dir." && /usr/bin/nohup ".$processName." ".$dir."manage.py runserver --host=0.0.0.0 &";
echo $cmd;
echo shell_exec($cmd);
        }
        catch (Exception $ex) {}
    }
    
    public function getPids($processName) {
        $out;
        exec("pidof $processName", $out);
        if(empty($out)) return null;
        $out = reset($out);
        return explode(' ', $out);
    }
    
    public function kill($pids) {
        if(!$pids) return;
        foreach ($pids as $pid)
            exec("kill 9 $pid"); //exec("kill -15 $pid");
    }
}

function main() {
    $processName = "/home/wmbroker/.virtualenv/gateis_tapin/bin/python3.5";
    
    $demon   = new Demon();
    $process = new Process();
    
    if(!$demon->isExpiredByLastStartTime()) return;
    if($demon->isWorked()) return;
    
    echo "do restart\n";
    
    try {
        $pidsForKill = $process->getPids($processName);
        $process->kill($pidsForKill);
    } catch (Exception $ex) {}
    
    $demon->writeStartTime();
    $process->start($processName);
}
main();
