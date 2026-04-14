package com.learn.askthedoc.controller;


import com.learn.askthedoc.service.DocumentService;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;

@RestController
@RequestMapping("/api/docs")
public class DocumentController {

    private final DocumentService service;

    public DocumentController(DocumentService service){
        this.service= service;
    }


    @PostMapping("/upload")
    public ResponseEntity<String> uploadFile(@RequestParam("file")MultipartFile file){

        try {
            String uploadDir = "C:/rag-uploads/";
            File dir = new File(uploadDir);
            if(!dir.exists()) dir.mkdirs();
            String originalFileName = file.getOriginalFilename();
            String safeFileName = originalFileName.replaceAll("[^a-zA-Z0-9\\.\\-]", "_");
            String filePath = uploadDir + safeFileName;
            try {
                file.transferTo(new File(filePath));
            } catch (IOException e) {
                throw new RuntimeException(e);
            }

            service.saveDocument(file.getOriginalFilename(), filePath);
            return  ResponseEntity.ok("File uploaded Successfully");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Upload failed: " +e.getMessage());
        }

    }
}
