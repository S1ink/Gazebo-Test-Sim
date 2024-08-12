import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch.actions import AppendEnvironmentVariable
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():

	pkg_path = get_package_share_directory('lance_sim')
	ros_gz_sim = get_package_share_directory('ros_gz_sim')
	nav2_bringup = get_package_share_directory('nav2_bringup')

	launch_file_dir = os.path.join( pkg_path, 'launch' )
	worlds_path = os.path.join( pkg_path, 'worlds' )

	artemis_arena_world = os.path.join( worlds_path, 'artemis-arena.world' )
	maze_world = os.path.join( worlds_path, 'maze.world' )
	moon_world = os.path.join( worlds_path, 'moon.world' )
	arch_arena = os.path.join( worlds_path, 'arch-arena.world' )

	world_dict = {
		'arena' : artemis_arena_world,
		'maze' : maze_world,
		'moon' : moon_world,
		'arch' : arch_arena
	}
	
	# config arg for choosing which map to use

	# set env vars
	set_env_vars_resources = AppendEnvironmentVariable(
		'GZ_SIM_RESOURCE_PATH',
		os.path.join(pkg_path, 'description')
	)
	# launch gazebo server with the arena SDF
	gzserver_cmd = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
		),
		launch_arguments={
			'gz_args': ['-r -s -v4 ', world_dict.get(LaunchConfiguration('gz_map', default='arch'), artemis_arena_world)],
			'on_exit_shutdown': 'true',
			'pause': 'true'
		}.items()
	)
	# start gazebo client
	gzclient_cmd = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
		),
		launch_arguments={'gz_args': '-g -v4 '}.items(),
		condition = IfCondition(LaunchConfiguration('gz_gui', default='true'))
	)
	# spawn the robot
	spawn_lance_cmd = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(launch_file_dir, 'spawn_lance.launch.py')
		)
	)
	# publish robot state to /tf
	robot_state_publisher_cmd = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(launch_file_dir, 'robot_state_publisher.launch.py')
		),
		launch_arguments = {'use_sim_time': 'true'}.items()
	)
	# slam
	slam_impl_cmd = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(launch_file_dir, 'slam.launch.py')
		),
		launch_arguments = {'use_sim_time': 'true'}.items()
	)
	# target state publisher
	teleop_node = Node(
		name = 'teleop_node',
		package = 'teleop_twist_joy',
		executable = 'teleop_node',
		output = 'screen',
		parameters = [os.path.join(pkg_path, 'config', 'xbox_controller.yaml')],
		remappings = [('/cmd_vel', '/joystick_cmd_vel')]
	)
	# foxglove
	foxglove_node = Node(
		name = 'foxglove_server',
		package = 'foxglove_bridge',
		executable = 'foxglove_bridge',
		output = 'screen',
		parameters = [os.path.join(pkg_path, 'config', 'foxglove_bridge.yaml'), {'use_sim_time': True}]
	)
	# nav2
	nav2_launch = IncludeLaunchDescription(
		PythonLaunchDescriptionSource(
			os.path.join(nav2_bringup, 'launch', 'navigation_launch.py')
		),
		launch_arguments = {'params_file' : os.path.join(pkg_path, 'config', 'nav2.yaml')}.items()
	)

	return LaunchDescription([
		DeclareLaunchArgument('gz_gui', default_value='false'),
		DeclareLaunchArgument('gz_map', default_value='arena'),
		set_env_vars_resources,
		gzserver_cmd,
		gzclient_cmd,
		robot_state_publisher_cmd,
		spawn_lance_cmd,
		slam_impl_cmd,
		teleop_node,
		# nav2_launch,
		foxglove_node
	])
