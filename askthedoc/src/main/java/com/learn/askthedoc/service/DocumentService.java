package com.learn.askthedoc.service;

import com.learn.askthedoc.entity.Document;
import com.learn.askthedoc.repository.DocumentRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class DocumentService {

    private final DocumentRepository repository;

    public DocumentService(DocumentRepository repository){
        this.repository = repository;
    }

    public Document saveDocument(String filename,String filePath){
        Document doc = new Document();
        doc.setFileName(filename);
        doc.setFilepath(filePath);
        doc.setUploadedAt(LocalDateTime.now());
        return repository.save(doc);
    }





}
