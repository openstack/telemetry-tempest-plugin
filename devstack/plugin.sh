# install_telemetry_tempest_plugin
function install_telemetry_tempest_plugin {
    setup_dev_lib "telemetry-tempest-plugin"
}

if [[ "$1" == "stack" ]]; then
    case "$2" in
        install)
            echo_summary "Installing telemetry-tempest-plugin"
            install_telemetry_tempest_plugin
            ;;
    esac
fi
