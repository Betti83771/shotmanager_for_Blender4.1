Shot Manager Python API
Main concepts
The add-on Shot Manager is made of 2 parts:

the Shot Manager itself (or SM), located in a 3D workspace and used to define and manipulate all the camera shots in a scene;
the Video Shot Manager (or VSM), located in a Video Sequence Editor workspace, it is dedicated to check the videos and exports (experimental at the moment)
Both parts are instanced located in a scene. There can be only one (or zero) instance of them in a given scene. The VSM needs a SM (and necesseraly have) in its owning scene.

Shot Manager
The Shot Manager is the main property class. Basically it contains a set of takes (CollectionProperty) and each take has a set of shots (CollectionProperty).

The functions available in the API are spread in several files, in a logical and object-oriented approach, according to the manipulated entities. They are not classes though, just C-like functions.

In Shot Manager the UI and functionnal part are - as much as possible - separated. 2 properties are a bit inbetween though: the current shot and the selected shot (they are indices, not pointers to the shot instances). The current shot is more than a UI information since the concerned shot has a special behavior (its camera is the one used by the scene for example). The selected shot refers to the highlighted item in the shots list (which is also the take). Many actions are based on it so it has also to be considered as a functional information. In spite of that the add-on can be completely manipulated without the use of the interface, and takes that are not set as the current one can be changed in exaclty the same way as the current one.

Video Shot Manager
The VSM is currently not exposed in the API.