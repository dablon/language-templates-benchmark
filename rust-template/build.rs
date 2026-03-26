fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .file_descriptor_set_path("proto descriptor.bin")
        .compile(&["../proto/service.proto", "../proto/common.proto"], &["../proto"])?;
    Ok(())
}