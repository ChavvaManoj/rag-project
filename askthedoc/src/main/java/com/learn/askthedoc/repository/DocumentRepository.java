package com.learn.askthedoc.repository;

import com.learn.askthedoc.entity.Document;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DocumentRepository extends JpaRepository<Document,Long> {
}
