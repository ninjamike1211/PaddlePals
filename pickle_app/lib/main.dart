import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'dart:async';
import 'package:permission_handler/permission_handler.dart';


void main() {
  runApp(const MyApp());
}

class User {
  // final int userId;
  final String username;
  // final String passwordHash;
  // final int valid;
  final int gamesPlayed;
  final int gamesWon;
  final double avgScore;

  User({
    // required this.userId,
    required this.username,
    // required this.passwordHash,
    // required this.valid,
    required this.gamesPlayed,
    required this.gamesWon,
    required this.avgScore
  });

  factory User.fromJson(Map<String, dynamic> json){
    return User(
      username: json['username'],
      gamesPlayed: json['gamesPlayed'],
      gamesWon: json['gamesWon'],
      avgScore: json['averageScore']
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'gamesPlayed': gamesPlayed,
    'gamesWon': gamesWon,
    'averageScore': avgScore
  };
}

List<User> usersList = [];

/*
CLASS FOR ALL API REQUESTS
 */
class APIRequests {
  final String url = "http://10.0.0.188:80";

  //GET REQUEST
  Future<Map<String, dynamic>> getUserRequest(int id_num) async {
    //"/pickle/user/get?user_id=1"
    Map<String, int> u_id = {
      'user_id': id_num,
    };

    print(u_id);
    String endpoint = "/pickle/user/get";

    //NOTE Authorization header for authorization api (look up standard authorization header, Bearer)

    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(u_id),
    );

    print("Sent JSON: ${jsonEncode(u_id)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> postNewUserRequest(String un, String pw) async {
    print(un);
    print(pw);
    Map<String, String> newUser = {
      'username': un.trim(),
      'password': pw.trim(),
    };

    print(newUser);
    String endpoint = "/pickle/user/create";


    final response = await http.post(
      Uri.parse('$url$endpoint'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: json.encode(newUser),
    );

    print("Sent JSON: ${jsonEncode(newUser)}");
    print("Status: ${response.statusCode}");
    print("Body: ${response.body}");

    if (response.statusCode == 200 || response.statusCode == 201){
      return json.decode(response.body);
    }
    else{
      throw Exception('POST request failed: ${response.statusCode}, body: ${response.body}');
    }
  }
}

final api = APIRequests();

class BleFunctionality{

  final FlutterReactiveBle flutterReactiveBle = FlutterReactiveBle();
  final List<DiscoveredDevice> devices = [];
  late StreamSubscription<DiscoveredDevice> scanSubscription;
  late StreamSubscription<ConnectionStateUpdate> connection;
  DiscoveredDevice? connectedDevice;

  BleFunctionality();

  Future<bool> requestPermissions() async {
    final status = await [
      Permission.location,
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
    ].request();

    return status.values.every((s) => s.isGranted);
  }

  Future<void> startScan({required void Function(DiscoveredDevice) onDeviceDiscovered}) async {
    bool granted = await requestPermissions();
    if(granted) {
      flutterReactiveBle.statusStream.listen((status) {
        if (status == BleStatus.ready) {
          print("Ready for BLE discovery");
          scanSubscription = flutterReactiveBle
              .scanForDevices(withServices: <Uuid>[])
              .listen((device) {
            // Add to list if not already present
            final known = devices.any((d) => d.id == device.id);
            if (!known) {
              devices.add(device);
              onDeviceDiscovered(device);
            }
          }, onError: (error) {
            print('Scan error: $error');
          });
        }
        else {
          print("BLE status: $status ");
        }
      });
    }
    else{
      print("Permissions not granted");
    }
  }

  Future<void> connectDevice(DiscoveredDevice selectedDevice, void Function(bool) connectionStatus) async {
    connection = flutterReactiveBle.connectToDevice(id: selectedDevice.id).listen((connectionState) {
      print("Connection State for device ${selectedDevice
          .name} : ${connectionState.connectionState}");
      if (connectionState.connectionState == DeviceConnectionState.connected) {
        connectionStatus(true);
        connectedDevice = selectedDevice;
        print("connected");
      }
      else if (connectionState.connectionState ==
          DeviceConnectionState.disconnected) {
        connectionStatus(false);
        connectedDevice = null;
        print("disconnected");
      }
    }, onError: (Object error){
      print("Connecting to device resulted in error $error");
    });
  }

  void readLiveFromDevice({
    required DiscoveredDevice connectedDevice,
    required Uuid serviceUuid,
    required Uuid characteristicUuid,
    required Function(String) onData,
    required Function(String) onError,
  }){


    final characteristic = QualifiedCharacteristic(
        characteristicId: characteristicUuid,
        serviceId: serviceUuid,
        deviceId: connectedDevice.id);

    final response = flutterReactiveBle.subscribeToCharacteristic(characteristic).listen(
          (data) {
        // Convert List<int> to readable value
        final stringValue = String.fromCharCodes(data);
        print("read $stringValue");
        onData(stringValue);
      },
      onError: (error) {
        onError("Error reading string data $error");
      },
    );
  }
}

final myBLE = BleFunctionality();

class Game {
  bool inProgress = false;
  bool isFinished = false;
  int myScore = 0;
  int opponentScore = 0;
  bool playingWithFriend = false;
  String opponentName = "Opponent";
  String winner = "";

  void incMyScore(){
    myScore += 1;
  }

  void incOppScore(){
    opponentScore += 1;
  }

  bool checkForWinner(){
    if (myScore >= 11 && opponentScore <= myScore - 2){
      inProgress = false;
      isFinished = true;
      return true;
    }
    else if(opponentScore >= 11 && myScore <= opponentScore - 2){
      inProgress = false;
      isFinished = true;
      return true;
    }
    else{
      return false;
    }
  }

  String getWinner(){
    if (checkForWinner()){
      if (myScore > opponentScore) {
        winner = "me";
        return winner;
      }
      else{
        winner = "opponent";
        return winner;
      }
    }
    else{
      return "no winner";
    }
  }

  void startGame(){
    inProgress = true;
  }

}

class MyTextEntryWidget extends StatefulWidget {
  @override
  _MyTextEntryWidgetState createState() => _MyTextEntryWidgetState();
}

class _MyTextEntryWidgetState extends State<MyTextEntryWidget> {
  final TextEditingController _controller1 = TextEditingController();
  final TextEditingController _controller2 = TextEditingController();

  _createNewUser(String userName, String password) {
    // final newUser = User(
    //   username: newName,
    //   gamesPlayed: 0,
    //   gamesWon: 0,
    //   avgScore: 0
    // );

    // usersList.add(newUser);

    api.postNewUserRequest(userName, password);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          TextField(
            controller: _controller1,
            decoration: InputDecoration(
              labelText: 'Enter username',
              border: OutlineInputBorder(),
            ),
          ),
          SizedBox(
            height: 16,
          ),
          TextField(
            controller: _controller2,
            decoration: InputDecoration(
              labelText: 'Enter password',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: (){
              _createNewUser(_controller1.text, _controller2.text);
            },
            child: const Text('Create'),
          )
        ],
      ),
    );
  }
}


//User will probably be an app state
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.tealAccent),
      ),
      home: MyHomePage(),
    );
  }
}

class MyHomePage extends StatefulWidget {
  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {

  var selectedIndex = 0;


  @override
  Widget build(BuildContext context) {
    Widget page;
    switch (selectedIndex) {
      case 0:
        page = GamePage();
        break;
      case 1:
        page = SocialPage();
        break;
      case 2:
        page = HistoryPage();
        break;
      case 3:
        page = ProfilePage();
        break;
      case 4:
        page = newUserPage();
        break;
      default:
        throw UnimplementedError('no widget for $selectedIndex');
    }

    return LayoutBuilder(
        builder: (context, constraints) {
          return Scaffold(
            body: Row(
              children: [
                SafeArea(
                  child: NavigationRail(
                    extended: constraints.maxWidth >= 600,
                    destinations: [
                      NavigationRailDestination(
                        icon: Icon(Icons.sports_tennis),
                        label: Text('Games'),
                      ),
                      NavigationRailDestination(
                        icon: Icon(Icons.groups),
                        label: Text('My Pals'),
                      ),
                      NavigationRailDestination(
                        icon: Icon(Icons.history),
                        label: Text('History'),
                      ),
                      NavigationRailDestination(
                          icon: Icon(Icons.person),
                          label: Text('ProfileS')
                      ),
                      NavigationRailDestination(
                          icon: Icon(Icons.add),
                          label: Text('Add User'))
                    ],
                    selectedIndex: selectedIndex,
                    onDestinationSelected: (value) {
                      setState(() {
                        selectedIndex = value;
                      });
                    },
                  ),
                ),
                Expanded(
                  child: Container(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    child: page,
                  ),
                ),
              ],
            ),
          );
        }
    );
  }
}

class GamePage extends StatefulWidget{
  const GamePage({super.key});

  @override
  State<GamePage> createState() => _GamePageState();
}

class _GamePageState extends State<GamePage> {
  final game = Game();
  final serviceUuid = Uuid.parse("your-service-uuid");
  final characteristicUuid = Uuid.parse("your-char-uuid");


  String getTitle(){
    String title = "";
    if (game.inProgress){
      title = "Current Game";
    }
    else if (game.isFinished){
      title = "Finished Game";
    }
    else{
      title = "Start a Game";
    }

    return title;
  }

  //class Game variable
  //title changes if game is started
  //change page look if no connectedDevice

  //subscribe to characteristics here
  @override
  void initState() {
    super.initState();
    if(myBLE.connectedDevice != null){
     DiscoveredDevice device = myBLE.connectedDevice!;

     myBLE.readLiveFromDevice(
         connectedDevice: device,
         serviceUuid: serviceUuid,
         characteristicUuid: characteristicUuid,
         onData: (data) {
           setState(() {
             game.myScore = int.tryParse(data) ?? 0;
           });
         },
         onError: (error) {
           setState(() {
             game.myScore = -1;
           });
         },
     );
    }

  }

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: Text(
          getTitle()
        ),
      ),
      body:
        Column(
          children: [
            Row(
              children: [
                SizedBox(width: 80,),
                Text(
                  "Me",
                  style: TextStyle(
                    fontSize: 24
                  ),
                ),
                SizedBox(width: 70,), //,may need to make spacing variable depending opponentName
                Text(
                  game.opponentName,
                  style: TextStyle(
                      fontSize: 24
                  ),
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  height: 200,
                  width: 125,
                  decoration:BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    border: Border.all(
                      color: Colors.black,
                      width: 2
                    )
                  ),
                  alignment: Alignment.center,
                  child: Text(
                      game.myScore.toString(),
                      style: TextStyle(
                        fontSize: 40
                      ),
                  ),

                ),
                SizedBox(width: 16),
                Container(
                    height: 200,
                    width: 125,
                    decoration:BoxDecoration(
                        color: Theme.of(context).colorScheme.primaryContainer,
                        border: Border.all(
                            color: Colors.black,
                            width: 2
                        )
                    ),
                    alignment: Alignment.center,
                    child: Text(
                        game.opponentScore.toString(),
                        style: TextStyle(
                            fontSize: 40
                        ),
                    )
                ),
              ],
            ),
            Text("Message 1"),
          ],
        ),
      );
  }
}

class SocialPage extends StatelessWidget{
  const SocialPage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Pals'),
      ),
      body: Center(
        child: Container( //PUT LIST OF FRIENDS
          width: 100,
          height: 100,
          color: Colors.blue,
          child: Text('Hello'),
        ),
      ),
    );
  }
}

class HistoryPage extends StatelessWidget{
  const HistoryPage({super.key});

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('History\n(View Stats from Database)'),
      ),
      body: Center(
        child: FutureBuilder<Map<String, dynamic>>(
            future: api.getUserRequest(9),
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const CircularProgressIndicator();
              } else if (snapshot.hasError) {
                return Text('Error: ${snapshot.error}');
              } else if (!snapshot.hasData || snapshot.data!.isEmpty) {
                return const Text('No user data available');
              }

              final userData = snapshot.data!;
              final user = User.fromJson(userData);

              return Text(
                  'Username: ${user.username}\n'
                  'Games Played: ${user.gamesPlayed}\n'
                  'Games Won: ${user.gamesWon}\n'
                      'Average Points per Game: ${user.avgScore}',
                style: TextStyle(
                  fontSize: 18,
                ),
              );
            },
        ), //FutureBuilder
      ), //Center
    );
  }
}

class newUserPage extends StatefulWidget{
  const newUserPage({super.key});

  @override
  State<newUserPage> createState() => _newUserPageState();
}

class _newUserPageState extends State<newUserPage> {

  @override
  Widget build(BuildContext context){
    return Scaffold(
      appBar: AppBar(
        title: const Text('Add User'),
      ),
      body: Center(
        child: Column(
          children: [
            MyTextEntryWidget(),
          ],
        ),
      ),
    );
  }
}

class ProfilePage extends StatefulWidget{
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  bool isConnected = false;

  void scan(){
    myBLE.startScan(onDeviceDiscovered: (device) {
      setState(() {}); // Trigger rebuild; myBLE.devices is already updated
    });
  }

  void connect(DiscoveredDevice device){
    print("Pressed");
    myBLE.connectDevice(device, (bool status) {
      setState(() {
        isConnected = status;
      });
      print("Connection status updated: $status");
    });

  }

  void initState() {
    super.initState();
    scan();
  }

  @override
  Widget build(BuildContext context){
    final List<DiscoveredDevice> devices = myBLE.devices;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Your Profile'),
      ),
      body: Center(
        child: Column(
          children: [
            Container(
              width: 100,
              height: 100,
              color: Colors.blue,
            ),
            SizedBox(height: 16),
            Text(
              "Username:"
            ),
            SizedBox(height: 16,),
            Expanded(
              child: ListView.builder(
              itemCount: devices.length,
              itemBuilder: (context, index) {
                final device = devices[index];
                return ListTile(
                  title: Text(device.name.isNotEmpty ? device.name : "Unnamed"),
                  subtitle: Text(device.id),
                  //trailing: Text("RSSI: ${device.rssi}"),
                  onTap: () => connect(device),
                );
              }
              ),
            ),
            ElevatedButton(
                onPressed: scan,
                child: Text("Rescan")
            )
          ],
        ),
      ),
    );
  }
}

